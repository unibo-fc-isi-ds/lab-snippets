{
  description = "Develop Python on Nix with poetry";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = {nixpkgs, ...}: let
    inherit (nixpkgs) lib;
    forAllSystems = lib.genAttrs lib.systems.flakeExposed;
  in {
    devShells = forAllSystems (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        default = pkgs.mkShell {
          packages = [
            pkgs.python314
            pkgs.poetry
          ];

          buildInputs = [
            pkgs.wayland
            pkgs.libxkbcommon
            pkgs.libGL
            pkgs.mesa
          ];

          LD_LIBRARY_PATH = lib.makeLibraryPath [
            pkgs.wayland
            pkgs.libxkbcommon
            pkgs.libGL
            pkgs.mesa
          ];

          shellHook = ''
            unset PYTHONPATH
            export POETRY_VIRTUALENVS_IN_PROJECT=true
            poetry install
            source .venv/bin/activate
          '';
        };
      }
    );
  };
}
