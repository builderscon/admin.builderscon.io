package Octav::AdminWeb::DateTime;
use strict;
use DateTime::TimeZone;
use DateTime::TimeZone::Catalog;
use DateTime::Format::RFC3339;

sub timezones {
    return \@DateTime::TimeZone::Catalog::ALL;
}

my $rfc3339 = DateTime::Format::RFC3339->new();
sub concat_time {
    my ($date, $time, $tz) = @_;

    if ($time =~ /^\d\d:\d\d$/) {
        $time .= ":00";
    }

    my $offset;
    if ($tz eq 'UTC') {
        $offset = 'Z';
    } else {
        my $tz_obj = DateTime::TimeZone->new(name => $tz);
        $offset = DateTime::TimeZone->offset_as_string($tz_obj->offset_for_datetime(DateTime->now()));
        $offset =~ s/^([+-]\d{2})(\d{2})$/$1:$2/;
    }
    return "${date}T${time}${offset}"
}


