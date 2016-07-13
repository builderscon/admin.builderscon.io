package Octav::AdminWeb::Controller::Venue;
use Mojo::Base qw(Mojolicious::Controller);
use JSON::Types ();

has columns => sub { 
    return ["name", "name#ja", "address", "address#ja", "latitude", "longitude"];
};

sub list {
    my $self = shift;

    my $client = $self->client();
    my $venues = $client->list_venue();
    $self->stash(venues => $venues);
    $self->render(tx => "venue/list");
}

sub _lookup {
    my $self = shift;

    my $log = $self->app->log;
    my $id = $self->param('id');
    if (!$id) {
        $log->debug("No 'id' available in query");
        $self->render(text => "not found", status => 404);
        return
    }

    my $client = $self->client;
    my $venue = $client->lookup_venue({id => $id, lang => "all"});
    if (! $venue) {
        $log->debug("No such venue '$id'");
        $self->render(text => "not found", status => 404);
        return
    }
    $self->stash(venue => $venue);
    $self->stash(api_key => $self->config->{googlemaps}->{api_key});
    return 1
}

sub lookup {
    my $self = shift;
    if (! $self->_lookup()) {
        return
    }
    $self->render(tx => "venue/lookup");
}

sub edit {
    my $self = shift;
    if (! $self->_lookup()) {
        return
    }
    $self->render(tx => "venue/edit");
}

sub update {
    my $self = shift;

    my $id = $self->param('id');
    if (!$id) {
        return $self->render(text => "not found", status => 404);
    }

    my $client = $self->client;
    my $venue = $client->lookup_venue({id => $id, lang => "all"});

    my %params = (
        id => $id,
        user_id => $self->stash('ui_user')->{id}),
    );
    for my $pname (@{$self->columns}) {
        my $pvalue = $self->param($pname);
        if ($pvalue ne $venue->{$pname}) {
            if ($pname =~ /^(?:latitude|longitude)$/) {
                $pvalue = JSON::Types::number($pvalue);
            }
            $params{$pname} = $pvalue;
        }
    }

    if (!$client->update_venue(\%params)) {
        die $client->last_error();
    }

    $self->redirect_to($self->url_for('/venue/lookup')->query(id => $id));
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
        $self->stash(venue => $h->{params});
    }

    $self->render(tx => "venue/edit");
}

# This does the validation and creates the entry.
sub create {
    my $self = shift;

    my %params = (user_id => $self->stash('ui_user')->{id});
    for my $pname (@{$self->columns}) {
        my $pvalue = $self->param($pname);
        if ($pname =~ /^(?:latitude|longitude)$/) {
            $pvalue = JSON::Types::number($pvalue);
        }
        $params{$pname} = $pvalue;
    }

    my $client = $self->client;
    my $venue = $client->create_venue(\%params);
    if (!$venue) {
        # XXX Currently we don't have a great way to show errors
        # we just take the returned error, and shove it in the session
        my $id = Digest::SHA::sha1_hex(time() . {} . rand() . $$);
        $self->plack_session->{$id} = {
            error => $client->last_error(),
            params => \%params,
        };
        $self->redirect_to($self->url_for("/venue/input")->query(error => $id));
        return
    }

    $self->redirect_to($self->url_for("/venue/lookup")->query(id => $venue->{id}));
}


1;