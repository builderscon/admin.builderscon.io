package Octav::AdminWeb::Controller::Conference;
use Mojo::Base qw(Mojolicious::Controller);
use Mojo::Util ();

sub list {
    my $self = shift;

    my $client = $self->client();
    my $conferences = $client->list_conference({status => "any"});
    $self->stash(conferences => $conferences);
    $self->render(tx => "conference/list");
}

sub _lookup {
    my $self = shift;

    my $id = $self->param('id');
    if (!$id) {
        $self->render(text => "not found", status => 404);
        return;
    }

    return $self->_lookup_conference_id($id);
}

sub _lookup_conference_id {
    my $self = shift;
    my $id = shift;
    my $client = $self->client;
    my $conference = $client->lookup_conference({id => $id, lang => "all"});
    if (!$conference) {
        $self->render(text => "conference not found", status => 404);
        return;
    }
    $self->stash(api_key => $self->config->{googlemaps}->{api_key});
    $self->stash(conference => $conference);
    return 1
}

sub lookup {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }
    $self->render(tx => "conference/lookup");
}

sub edit {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }

    my $client = $self->client();
    # XXX We should cache this
    $self->stash(series => $client->list_conference_series());
    $self->stash(venues => $client->list_venue());
    $self->render(tx => "conference/edit");
}

sub update {
    my $self = shift;

    my $id = $self->param('id');
    if (!$id) {
        return $self->render(text => "not found", status => 404);
    }

    my $client = $self->client;
    my $conference = $client->lookup_conference({id => $id, lang => "all"});

    my @columns = ("title", "sub_title", "title#ja", "sub_title#ja", "slug", "description", "description#ja", "cfp_lead_text", "cfp_lead_text#ja", "cfp_pre_submit_instructions", "cfp_pre_submit_instructions#ja", "cfp_post_submit_instructions", "cfp_post_submit_instructions#ja");
    my %params = (id => $id, user_id => $self->stash('ui_user')->{id});
    for my $pname (@columns) {
        my $pvalue = $self->param($pname);
        if ($pvalue ne $conference->{$pname}) {
            $params{$pname} = $pvalue;
        }
    }

    my @guards;
    foreach my $field (qw(cover)) {
        if (my $upload = $self->req->upload($field)) {
            if ($upload->size <= 0) {
                next;
            }
            # Move this to a temporary location so it can be passed to 
            # add_sponsor, and uploaded
            my $f = File::Temp->new();
            $f->unlink_on_destroy(1);
            $upload->move_to($f->filename);
            $params{$field} = $f->filename;
            push @guards, $f;
        }
    }

    if (!$client->update_conference(\%params)) {
        die $client->last_error();
    }

    $self->redirect_to($self->url_for('/conference/lookup')->query(id => $id));
}

# This is just shows the form to create
sub input {
    my $self = shift;

    # If we have been redirected here because of a validation error,
    # we should remember the values
    my $h;
    my $error_id = $self->param("error");
    if ($error_id && (my $h = delete $self->plack_session->{$error_id})) {
        $self->stash(error => $h->{error});
        $self->stash(conference => $h->{params});
    }

    $self->render(tx => "conference/input");
}

# This does the validation and creates the entry.
sub create {
    my $self = shift;

    my @columns = ("title", "sub_title", "title#ja", "sub_title#ja", "slug", "description", "description#ja", "cfp_lead_text", "cfp_lead_text#ja", "cfp_pre_submit_instructions", "cfp_pre_submit_instructions#ja", "cfp_post_submit_instructions", "cfp_post_submit_instructions#ja");
    my %params = (user_id => $self->stash('ui_user')->{id});
    for my $pname (@columns) {
        my $pvalue = $self->param($pname);
        if ($pvalue) {
            $params{$pname} = $pvalue;
        }
    }

    my $client = $self->client;
    my $conference = $client->create_conference(\%params);
    if (!$conference) {
        # XXX Currently we don't have a great way to show errors
        # we just take the returned error, and shove it in the session
        my $id = Digest::SHA::sha1_hex(time() . {} . rand() . $$);
        $self->plack_session->{$id} = {
            error => $client->last_error(),
            params => \%params,
        };
        $self->redirect_to($self->url_for("/conference/input")->query(error => $id));
        return
    }

    $self->redirect_to($self->url_for("/conference/lookup")->query(id => $conference->{id}));
}

sub date_add {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }

    my %params = (
        conference_id => $self->stash("conference")->{id},
        dates => [ {
            date => $self->param("date"),
            open => $self->param("open"),
            close => $self->param("close"),
        } ],
        user_id => $self->stash('ui_user')->{id},
    );
    my $client = $self->client;
    if (! $client->add_conference_dates(\%params)) {
        # XXX handle this properly
        die $client->last_error();
    }

    $self->redirect_to($self->url_for("/conference/lookup")->query(id => $self->stash("conference")->{id}));
}

sub date_remove {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }

    my %params = (
        conference_id => $self->stash("conference")->{id},
        dates => [ {
            date => $self->param("date"),
            open => $self->param("open"),
            close => $self->param("close"),
        } ],
        user_id => $self->stash('ui_user')->{id},
    );
    my $client = $self->client;
    if (! $client->delete_conference_dates(\%params)) {
        # XXX handle this properly
        die $client->last_error();
    }

    $self->redirect_to($self->url_for("/conference/lookup")->query(id => $self->stash("conference")->{id}));
}

sub venue_add {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }

    my %params = (
        conference_id => $self->stash("conference")->{id},
        venue_id => $self->param("venue_id"),
        user_id => $self->stash('ui_user')->{id},
    );
    my $client = $self->client;
    if (! $client->add_conference_venue(\%params)) {
        # XXX handle this properly
        die $client->last_error();
    }

    $self->redirect_to($self->url_for("/conference/lookup")->query(id => $self->stash("conference")->{id}));
}

sub venue_remove {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }

    my %params = (
        conference_id => $self->stash("conference")->{id},
        venue_id => $self->param("venue_id"),
        user_id => $self->stash('ui_user')->{id},
    );
    my $client = $self->client;
    if (! $client->delete_conference_venue(\%params)) {
        # XXX handle this properly
        die $client->last_error();
    }

    $self->redirect_to($self->url_for("/conference/lookup")->query(id => $self->stash("conference")->{id}));
}

sub featured_speaker_add {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }

    my %params = (
        conference_id => $self->stash("conference")->{id},
        user_id => $self->stash('ui_user')->{id},
    );

    my @columns = ("avatar_url", "display_name", "description", "display_name#ja", "description#ja");
    foreach my $column (@columns) {
        if (my $v = $self->param($column)) {
            $params{$column} = $v;
        }
    }
    my $client = $self->client;
    if (! $client->add_featured_speaker(\%params)) {
        # XXX handle this properly
        die $client->last_error();
    }

    $self->redirect_to($self->url_for("/conference/lookup")->query(id => $self->stash("conference")->{id}));
}

sub featured_speaker_remove {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }

    my %params = (
        conference_id => $self->stash("conference")->{id},
        id => $self->param("featured_speaker_id"),
        user_id => $self->stash('ui_user')->{id},
    );
    my $client = $self->client;
    if (! $client->delete_featured_speaker(\%params)) {
        # XXX handle this properly
        die $client->last_error();
    }

    $self->redirect_to($self->url_for("/conference/lookup")->query(id => $self->stash("conference")->{id}));
}

sub administrator_add {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }

    my %params = (
        conference_id => $self->stash("conference")->{id},
        user_id => $self->stash('ui_user')->{id},
    );

    my @columns = ("admin_id");
    foreach my $column (@columns) {
        if (my $v = $self->param($column)) {
            $params{$column} = $v;
        }
    }
    my $client = $self->client;
    if (! $client->add_conference_admin(\%params)) {
        # XXX handle this properly
        die $client->last_error();
    }

    $self->redirect_to($self->url_for("/conference/lookup")->query(id => $self->stash("conference")->{id}));
}

sub administrator_remove {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }

    my %params = (
        conference_id => $self->stash("conference")->{id},
        id => $self->param("id"),
        user_id => $self->stash('ui_user')->{id},
    );
    my $client = $self->client;
    if (! $client->delete_conference_admin(\%params)) {
        # XXX handle this properly
        die $client->last_error();
    }

    $self->redirect_to($self->url_for("/conference/lookup")->query(id => $self->stash("conference")->{id}));
}

sub sponsor_add {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }

    my %params = (
        conference_id => $self->stash("conference")->{id},
        user_id => $self->stash('ui_user')->{id},
    );

    my @columns = ("name", "url", "group_name", "name#ja");
    foreach my $column (@columns) {
        if (my $v = $self->param($column)) {
            $params{$column} = $v;
        }
    }

    my $client = $self->client;
    if (! $client->add_sponsor(\%params)) {
        # XXX handle this properly
        die $client->last_error();
    }

    $self->redirect_to($self->url_for("/conference/lookup")->query(id => $self->stash("conference")->{id}));
}

sub sponsor_remove {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }

    my %params = (
        conference_id => $self->stash("conference")->{id},
        id => $self->param("sponsor_id"),
        user_id => $self->stash('ui_user')->{id},
    );
    my $client = $self->client;
    if (! $client->delete_sponsor(\%params)) {
        # XXX handle this properly
        die $client->last_error();
    }

    $self->redirect_to($self->url_for("/conference/lookup")->query(id => $self->stash("conference")->{id}));
}

sub sessions {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }

    my %params = (
        conference_id => $self->stash("conference")->{id},
        user_id => $self->stash('ui_user')->{id},
        status => [ "pending", "accepted", "rejected" ],
    );
    my $client = $self->client;
    my $sessions = $client->list_sessions(\%params);
    if (!$sessions) {
        die $client->last_error
    }

    $self->stash(sessions => $sessions);
    $self->render(tx => "conference/sessions");
}

sub bulk_update_sessions {
    my $self = shift;
    my $body = Mojo::Util::url_unescape($self->req->body);
    my $payload = JSON::decode_json($body);

    if (! $self->_lookup_conference_id($payload->{id})) {
        return
    }

    my $client = $self->client;
    for my $p (@{$payload->{sessions}}) {
        my $ok = $client->update_session({
            %$p,
            user_id => $self->stash('ui_user')->{id},
        });
        if (! $ok) {
            die $client->last_error;
        }
    }

    $self->redirect_to($self->url_for("/conference/sessions")->query(id => $self->stash("conference")->{id}));
}
1;
