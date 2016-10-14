requires 'perl', '5.008001';

on 'build' => sub {
    requires 'Module::Build::Tiny', '0.035';
};

on 'test' => sub {
    requires 'Test::More', '0.98';
};

requires 'DateTime';
requires 'DateTime::TimeZone';
requires 'DateTime::Format::RFC3339';
requires 'File::LibMagic';
requires 'HTML::Scrubber';
requires 'IO::Socket::SSL' => ">= 1.94";
requires 'JSON';
requires 'JSON::Types';
requires 'Mojolicious';
requires 'Mojolicious::Plugin::XslateRenderer';
requires 'Net::Twitter';
requires 'Plack';
requires 'Plack::Middleware::Auth::Basic';
requires 'Plack::Middleware::Session::Simple';
requires 'Redis::Jet';
requires 'Sereal';
requires 'Server::Starter';
requires 'Starlet';
requires 'Text::Markdown';
requires 'Text::Xslate::Bridge::TT2Like';
requires 'UUID::Tiny';
