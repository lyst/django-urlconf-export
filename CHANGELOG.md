# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2020-06-06
### Changed
- Update django in pipfile.lock to address a security vulnerability.
- Fix regression following release of check-manifest 0.42: --ignore syntax was changed.

## [1.1.0] - 2020-03-31
### Added
- Add setting to specify which module to import URLconf into: URLCONF_IMPORT_ROOT_URLCONF
- Add helper method to initialize in non-Django services
### Changed
- Breaking change: when importing, existing URLconf in target module will be overwritten. It used to be appended.
- Re-order README sections, and add integration examples
- Correction to README: whitelist and blacklist are sets not lists

## [1.0.4] - 2020-03-16
### Added
- Unit tests for urlconf_qa module

## [1.0.3] - 2020-03-16
### Changed
- Make all README.md links absolute, so they work in PyPi description

## [1.0.2] - 2020-03-16
### Changed
- Make images show up in PyPi description

## [1.0.1] - 2020-03-16
### Changed
- Include README.md in PyPi package description

## [1.0.0] - 2020-03-16
### Added
- Initial public release of the library
