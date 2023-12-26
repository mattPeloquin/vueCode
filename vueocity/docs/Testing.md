
Testing Overview
================
See [testing/ReadMe.md](testing/ReadMe.md) for notes on using test tools.

Automated tests are the primary quality control focus. Manual testing is used mostly for new development. Testing goals are efficiency and high-leverage coverage. MPF is data driven; high-value equivalence cases are a key factor in test design, and randomization is used to provide coverage over time.

Automated testing is grouped LOOSELY into two groups:

    Unit / Module / App / Model / View / API
      - Local run of class, module, model, and/or view/endpoint/api - No AWS
      - More fixed and repeatable, little random input, some fixture use
      - Always fresh DB, usually run locally
      - Tests are independent, no dependency or order
      - Must have option to run quickly (entire test set can be run < 4 min)
      - Tests are timed to monitor baseline performance, but no load testing

    E2E / End-to-End / System / Load
      - Full system stack testing, run locally or on AWS
      - Mostly random input, NO use of fixture data
      - Can use fresh DB, existing DB or live site
      - May have dependencies in test ordering to support composing
      - Supports both fast smoke testing and open ended testing
      - Includes load testing for performance and scalability
      - UI and/or API/endpoint driven (Selenium and Locust)

# Manual Testing

Most manual testing is done during development. Informal testing may occur with staff or platform by partners.

    Manual testing is always ad hoc --> TEST CASES ARE NOT DOCUMENTED...

        ...IF A TEST CASE NEEDS DOCUMENTATION, IT SHOULD BE AUTOMATED!

Manual testing occurs as-needed using the environment and test data that is appropriate.

# Automated Testing

Where possible, introspection is used to drive Unit testing, while randomized simulation is used in E2E testing. Test code is a first-class citizen treated as production code. Automated testing may be created/packaged in one of the following:

- **Django model tests** *mpframework.testing.framework.model* \
Core python logic testing for app models.

- **Django view tests** *mpframework.testing.framework.view* \
Ensure urls resolve, exercise view and API logic. Django admin view introspection.

- **Selenium e2e tests** *mpframework.testing.e2e* \
Selenium scripts run either in local dev or against hosted site

- **Locust load Tests** *mpframework.testing.load* \
HTML calls to simulate user load

- **Code analysis** *(static code tests)* \
Using pyflakes to catch imports, syntax problems, and unused variables

- **Javascript Tests**\
FUTURE - Version2 of portal will add JS tests

- **Other tests, run as needed**\
Browser compatibility tests on external platforms.
Some Django test code is not included in default test verification and run manually because of side effects, speed, or need special environments.

# Local vs. Cloud Testing

Local tests are run in dev sandboxes, either on local dev machines or on dev servers. Test data fixtures are setup to allow use of local network IP addresses.

It is safe to run automated System tests against the live production site.
FUTURE - when overhead worth it, maintain a dev/staging environment.

# Coverage

FUTURE - quantify code/feature/module/screen/url coverage in some fashion.
