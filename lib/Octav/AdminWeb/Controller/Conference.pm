package Octav::AdminWeb::Controller::Conference;
use Mojo::Base qw(Mojolicious::Controller);

sub list {
    my $self = shift;

    my $client = $self->client();
    my $conferences = $client->list_conference();
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

    my $client = $self->client;
    my $conference = $client->lookup_conference({id => $id, lang => "all"});
    if (!$conference) {
        $self->render(text => "not found", status => 404);
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

    my @columns = ("title", "sub_title", "title#ja", "sub_title#ja", "slug");
    my %params = (id => $id, user_id => $self->stash('ui_user')->{id});
    for my $pname (@columns) {
        my $pvalue = $self->param($pname);
        if ($pvalue ne $conference->{$pname}) {
            $params{$pname} = $pvalue;
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

    my @columns = ("title", "sub_title", "title#ja", "sub_title#ja", "slug");
    my %params = (user_id => $self->stash('ui_user')->{id});
    for my $pname (@columns) {
        my $pvalue = $self->param($pname);
        $params{$pname} = $pvalue;
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
        dates => [ $self->param("date") ],
        user_id => $self->stash('ui_user')->{id}),
    );
    my $client = $self->client;
    if (! $client->add_conference_dates(\%params)) {
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
        user_id => $self->stash('ui_user')->{id}),
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
        user_id => $self->stash('ui_user')->{id}),
    );
    my $client = $self->client;
    if (! $client->delete_conference_venue(\%params)) {
        # XXX handle this properly
        die $client->last_error();
    }

    $self->redirect_to($self->url_for("/conference/lookup")->query(id => $self->stash("conference")->{id}));
}

1;
