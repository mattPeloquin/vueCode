
MPF Testing
===========

This folder contain global testing support:

    fixtures  - Data and resources loaded into clean dev DBs
    framework - General shared code for unit and E2E tests
    e2e       - Selenium system test cases and reusable code

Unit test code is embedded in 'tests' folders under apps.

# Local Ad-Hoc Bench Testing

    During development, automated tests are mixed with ad-hoc manual testing.
    A local dev server can be created with commands below and accessed at:

        http://127.0.0.1

        fab run         Supports local loopback testing only
        fab run-prod    Runs over network in non-debug mode (faster)
        fab clean       Reset the DB and ensure all code is up to date

    The test fixtures are loaded during a 'fab clean' - the fixtures include the following owner account for the default provider and sandbox, which is the entry point for local testing:

        user: owner@p1.com  password: mptest

    Most local testing assumes the default sandbox for the root domain will be used. To access sub-domains for local testing, use external DNS service like nip.io:

        http://p2sand1.127.0.0.1.nip.io

# Running Automated Tests

    Unit tests are self-contained Python code, no local server or other support is needed, typical examples:

        fab test              Default dev test, fast subset, in-memory DB
        fab test mpcontent    Run fast tests for just content apps
        fab test -l=2 -d=1    More comprehensive test coverage, on-disk DB

    E2E tests require browser and Selenium WebDriver support to be installed. Running typical examples is shown below:

        fab test-local                    Local server, which must be running
        fab test-local -t=random.forever  Runs tests in 'system.tests.random.forever'
        fab test-e2e -t=dev.newtests      New server/db for 'e2e.tests.dev.newtests'
        fab test-live --url=xyz.com       Tests on external server xyz.com, new site

    (smoke.basic are run as the default tests unless specified)

    Additional options for Selenium tests:

        wait=x  -- Add x second wait for each wait_point in code
        browser -- Define browser to launch
        runs=x  -- Repeat test x times

        fab test-local --wait=1.5
        fab test-local --runs=3 --browser=edge

    To turn up logging when running tests use log= and sl1=, sl2=, sl3=

        fab test --log=2 --sl1=cache
        fab test -l=1 --sl1=db --sl2=cache

# Online Browser Compatibility Testing

    Saucelabs probably has best plan for doing browsers in VMs

    Manual checks
    Setup Selenium tests to run on as-needed basis
