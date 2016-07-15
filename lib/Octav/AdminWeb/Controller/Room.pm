package Octav::AdminWeb::Controller::Room;
use Mojo::Base qw(Mojolicious::Controller);
use JSON::Types ();

has columns => sub { 
    return ["venue_id", "name", "name#ja", "capacity"]
};

sub list {
    my $self = shift;

    my $log = $self->app->log;
    my $venue_id = $self->param('venue_id');
    if (!$venue_id) {
        $log->debug("No 'venue_id' available in query");
        return $self->render(text => "not found", status => 404);
    }

    my $client = $self->client();
    my $rooms = $client->list_room({venue_id => $venue_id});
    $self->stash(rooms => $rooms);
    $self->render(tx => "room/list");
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
    my $room = $client->lookup_room({id => $id, lang => "all"});
    if (! $room) {
        $log->debug("No such room '$id'");
        $self->render(text => "not found", status => 404);
        return
    }
    $self->stash(room => $room);
    $self->stash(api_key => $self->config->{googlemaps}->{api_key});
    return 1
}

sub lookup {
    my $self = shift;
    if (! $self->_lookup()) {
        return
    }
    my $client = $self->client;
    my $venue = $client->lookup_venue({id => $self->stash('room')->{venue_id}});
    $self->stash(venue => $venue);
    $self->render(tx => "room/lookup");
}

sub edit {
    my $self = shift;
    if (! $self->_lookup()) {
        return
    }
    $self->render(tx => "room/edit");
}

sub update {
    my $self = shift;

    my $id = $self->param('id');
    if (!$id) {
        return $self->render(text => "not found", status => 404);
    }

    my $client = $self->client;
    my $room = $client->lookup_room({id => $id, lang => "all"});

    my %params = (
        id => $id,
        user_id => $self->stash('ui_user')->{id},
    );
    for my $pname (qw(name name#ja capacity)) {
        my $pvalue = $self->param($pname);
        if ($pvalue ne $room->{$pname}) {
            if ($pname =~ /^(?:latitude|longitude)$/) {
                $pvalue = JSON::Types::number($pvalue);
            }
            $params{$pname} = $pvalue;
        }
    }

    if (!$client->update_room(\%params)) {
        die "failed";
    }

    $self->redirect_to($self->url_for('room/lookup')->query(id => $id));
}

# This is just shows the form to create
sub input {
    my $self = shift;

    my $venue_id = $self->param("venue_id");
    if (! $venue_id ) {
        $self->render(text => "not found", status => 404);
        return
    }

    my $client = $self->client;
    my $venue = $client->lookup_venue({id => $venue_id});
    if (! $venue) {
        $self->render(text => "not found", status => 404);
        return
    }

    $self->stash(venue_id => $venue_id);

    # If we have been redirected here because of a validation error,
    # we should remember the values
    my $h;
    my $error_id = $self->param("error");
    if ($error_id && (my $h = delete $self->plack_session->{$error_id})) {
        $self->stash(error => $h->{error});
        $self->stash(room => $h->{params});
    }

    $self->render(tx => "room/input");
}

# This does the validation and creates the entry.
sub create {
    my $self = shift;

    my %params = (user_id => $self->stash('ui_user')->{id});
    for my $pname (@{$self->columns}) {
        my $pvalue = $self->param($pname);
        if ($pname eq 'capacity') {
            $pvalue = JSON::Types::number($pvalue);
        }
        $params{$pname} = $pvalue;
    }

    my $client = $self->client;
    my $room = $client->create_room(\%params);
    if (!$room) {
        # XXX Currently we don't have a great way to show errors
        # we just take the returned error, and shove it in the session
        my $id = Digest::SHA::sha1_hex(time() . {} . rand() . $$);
        $self->plack_session->{$id} = {
            error => $client->last_error(),
            params => \%params,
        };
        $self->redirect_to($self->url_for("/room/input")->query(error => $id));
        return
    }

    $self->redirect_to($self->url_for("/room/lookup")->query(id => $room->{id}));
}

1;