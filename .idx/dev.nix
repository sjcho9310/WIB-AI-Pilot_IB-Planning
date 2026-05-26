# To learn more about how to use Nix to configure your environment
# see: https://firebase.google.com/docs/studio/customize-workspace
{ pkgs, ... }: {
  channel = "stable-24.05";

  packages = [
    pkgs.flutter
    pkgs.jdk17
    pkgs.unzip
  ];

  env = {};

  idx = {2
    extensions = [
      "anthropic.claude-code"
      "Dart-Code.dart-code"
      "Dart-Code.flutter"
    ];

    workspace = {
      onCreate = {
        default.openFiles = [ "lib/main.dart" ];
      };
      onStart = {};
    };

    previews = {
      enable = true;
      previews = {
        android = {
          command = [
            "flutter"
            "run"
            "--machine"
            "-d"
            "android"
            "-d"
            "localhost:5555"
          ];
          manager = "flutter";
        };
        web = {
          command = [
            "flutter"
            "run"
            "--machine"
            "-d"
            "web-server"
            "--web-hostname"
            "0.0.0.0"
            "--web-port"
            "$PORT"
          ];
          manager = "flutter";
        };
      };
    };
  };
}
