package Octav::AdminWeb::Controller::User;
use Mojo::Base qw(Mojolicious::Controller);

sub dashboard {
    my $self = shift;
}

sub verify {
    my $self = shift;
    my $user = $self->_lookup();
    if (! $user) {
        return
    }

    my $client = $self->client();
    my %params = (
        id => $user->{id},
        user_id => $self->stash('ui_user')->{id},
    );
    $client->verify_user(\%params);
    $self->redirect_to($self->url_for("/user/lookup")->query(id => $user->{id}));
}

sub list {
    my $self = shift;

    my $client = $self->client();
    my @args;
    if (my $since = $self->param('since')) {
        push @args, (since => $since)
    }
    my $users = $client->list_user({@args});
    $self->stash(users => $users);
    $self->render(tx => "user/list");
}

sub _lookup {
    my $self = shift;

    my $id = $self->param('id');
    if (!$id) {
        $self->render(text => "not found", status => 404);
        return
    }

    my $client = $self->client;
    my $user = $client->lookup_user({id => $id, lang => "all"});
    if (! $user) {
        $self->render(text => "not found", status => 404);
        return
    }

    $self->stash(user => $user);
    return $user;
}

sub lookup {
    my $self = shift;
    my $user = $self->_lookup();
    if (! $user) {
        return
    }

    $self->render(tx => "user/lookup");
}

sub edit {
    my $self = shift;
    my $user = $self->_lookup();
    if (! $user) {
        return
    }

    $self->render(tx => "user/edit");
}

sub update {
    my $self = shift;
    my $user = $self->_lookup();
    if (! $user) {
        return
    }

    my %params = (
        id => $user->{id},
        user_id => $self->stash('ui_user')->{id},
    );
    for my $pname (qw(FIXME)) {
        my $pvalue = $self->param($pname);
        if ($pvalue ne $user->{$pname}) {
            $params{$pname} = $pvalue;
        }
    }

    my $client = $self->client;
    if (!$client->update_user(\%params)) {
        die "failed";
    }

    $self->redirect_to($self->url_for('/user/lookup')->query(id => $user->{id}));
}

1;
