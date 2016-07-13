package Octav::AdminWeb::Controller::ConferenceSeries;
use Mojo::Base qw(Mojolicious::Controller);

sub list {
    my $self = shift;

    my $client = $self->client();
    my $conference_series = $client->list_conference_series();
    $self->stash(conference_series => $conference_series);
    $self->render(tx => "conference_series/list");
}

sub _lookup {
    my $self = shift;

    my $id = $self->param('id');
    if (!$id) {
        $self->render(text => "not found", status => 404);
        return;
    }

    my $client = $self->client;
    my $conference_series = $client->lookup_conference_series({id => $id, lang => "all"});
    if (!$conference_series) {
        $self->render(text => "not found", status => 404);
        return;
    }
    $self->stash(api_key => $self->config->{googlemaps}->{api_key});
    $self->stash(conference_series => $conference_series);
    return 1
}

sub lookup {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }
    $self->render(tx => "conference_series/lookup");
}

sub edit {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }
    $self->render(tx => "conference_series/edit");
}

sub update {
    my $self = shift;

    my $id = $self->param('id');
    if (!$id) {
        return $self->render(text => "not found", status => 404);
    }

    my $client = $self->client;
    my $conference_series = $client->lookup_conference_series({id => $id, lang => "all"});

    my @columns = ("title", "sub_title", "title#ja", "sub_title#ja", "slug");
    my %params = (
        id => $id,
        user_id => $self->stash('ui_user')->{id}),
    );
    for my $pname (@columns) {
        my $pvalue = $self->param($pname);
        if ($pvalue ne $conference_series->{$pname}) {
            $params{$pname} = $pvalue;
        }
    }

    if (!$client->update_conference_series(\%params)) {
        die "failed";
    }

    $self->redirect_to($self->url_for('/conference_series/lookup')->query(id => $id));
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
        $self->stash(conference_series => $h->{params});
    }

    $self->render(tx => "conference_series/edit");
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
    my $conference_series = $client->create_conference_series(\%params);
    if (!$conference_series) {
        # XXX Currently we don't have a great way to show errors
        # we just take the returned error, and shove it in the session
        my $id = Digest::SHA::sha1_hex(time() . {} . rand() . $$);
        $self->plack_session->{$id} = {
            error => $client->last_error(),
            params => \%params,
        };
        $self->redirect_to($self->url_for("/conference_series/input")->query(error => $id));
        return
    }

    $self->redirect_to($self->url_for("/conference_series/lookup")->query(id => $conference_series->{id}));
}

1;