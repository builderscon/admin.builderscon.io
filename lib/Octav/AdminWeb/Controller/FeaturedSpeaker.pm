package Octav::AdminWeb::Controller::FeaturedSpeaker;
use Mojo::Base qw(Mojolicious::Controller);

sub _lookup {
    my $self = shift;

    my $id = $self->param('id');
    if (!$id) {
        $self->render(text => "not found", status => 404);
        return;
    }

    my $client = $self->client;
    my $featured_speaker = $client->lookup_featured_speaker({id => $id, lang => "all"});
    if (!$featured_speaker) {
        $self->render(text => "not found", status => 404);
        return;
    }

    my $conference = $client->lookup_conference({id => $featured_speaker->{conference_id}, lang => "all"});
    $self->stash(conference => $conference);
    $self->stash(featured_speaker => $featured_speaker);
    return 1
}

sub lookup {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }
use Data::Dumper;
warn Dumper($self->stash("featured_speaker"));
    $self->render(tx => "featured_speaker/lookup");
}

sub edit {
    my $self = shift;
    if (!$self->_lookup()) {
        return
    }

    my $client = $self->client();
    $self->render(tx => "featured_speaker/edit");
}

sub update {
    my $self = shift;

    my $id = $self->param('id');
    if (!$id) {
        return $self->render(text => "not found", status => 404);
    }

    my $client = $self->client;
    my $featured_speaker = $client->lookup_featured_speaker({id => $id, lang => "all"});

    my @columns = ("avatar_url", "speaker_id", "display_name", "description", "display_name#ja", "description#ja");
    my %params = (id => $id, user_id => $self->stash('ui_user')->{id});
    for my $pname (@columns) {
        my $pvalue = $self->param($pname);
        if ($pvalue ne $featured_speaker->{$pname}) {
            $params{$pname} = $pvalue;
        }
    }

use Data::Dumper;
warn Dumper(\%params);

    if (!$client->update_featured_speaker(\%params)) {
        die $client->last_error();
    }

    $self->redirect_to($self->url_for('/featured_speaker/lookup')->query(id => $id));
}

1;