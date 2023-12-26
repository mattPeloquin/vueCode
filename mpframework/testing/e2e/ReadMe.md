E2E Testing Framework
=====================

MPF E2E test code is built on Selenium. There is a layer in 'testing.framework.selenium' that makes accessing MPF UI easier. On top of that is a layer to facilitate code reuse, flexibility, and randomization described below.

E2E tests simulate human UI behavior. Tests fall into two broad categories:

    scripted - Data is randomized, test steps are ordered and repeatable
    random   - Test steps and data are randomized, can run indefinitely in any order

E2E test code is organized into the following folders:

    actions  - Independent, composable test cases
    blocks   - Stateful objects for web UI entities (user, content item, etc.)
    data     - Templates and support for randomized data
    stories  - Stateless routines that capture a series of common actions
    tests    - Test cases built with actions, stories, blocks, and data

Tests exercise mpframework base platform functionality. MPF extension and root platforms add E2E test code to cover their functionality.

# Test Design

## SystemTestCase

All test cases inherit from SystemTestCase (STC), which knows how to run tests either locally or on AWS. It wraps the Selenium web driver as 'self.sln', allowing both direct Selenium access and wrapping Selenium calls in helper methods. The STC also has 'self.owner', a user with owner privledges for a site, which is needed to start most testing.

An STC object is available in Block ('self.stc') and Story ('stc') code for performing Selenium operations. STCs hold some state (like what website to use), but test cases should avoid adding state to the STC. Tracking state in Blocks allows test cases and stories to be reused and composed into many combinations.

## Blocks

Blocks are STATEFUL data-driven classes that:

    1) Execute actions in the UI with randomized data
    2) Keep track of data they enter into the web UI
    3) Contain the majority of logic for interacting with web screens

Block methods enter randomized data into UI. Data entered/changed in the UI is stored in the block, so the block can find itself later in the UI and verify the data displays as expected.

Most blocks represent a specific UI entity which maps 1:1 with an admin screen like User, Content Item, Collection, Pricing Option, etc. Blocks may also be composed into groupings of related data that is tracked together.

## Data

All E2E tests use randomized data, which is passed to blocks.

The data folder holds data templates are dicts that define structure for randomized values.

## Stories

Stories are STATELESS functions that capture reusable test logic. Blocks are passed into stories, which manipulate the blocks, changing their state.

Stories and actions/test cases are similar, but stories are not stand-alone and they don't setup test state (e.g., which user is logged in). They are intended for reusable pieces of code used in actions/test cases.

## Actions

Actions are self-contained test cases that provide reuse and are the basis for random tests. They are not registered with Python unittest, so cannot be run directly.

Actions can execute in any order and in parallel. They have extra overhead compared to more specialized test cases (like smoke tests), as each action must setup context with login/logouts, new users, etc.

## Tests

The tests folder holds test cases that are the entry point for running E2E tests. Test cases use blocks, stories, actions, and other test cases to compose random and scripted tests.

Test cases are methods starting with 'test_' in classes inheriting from SystemTestCase, which is defined in 'e2e/tests/base.py'. The 'test_' methods are registered with Python unittest, and are run through the MPF test commands.

Scripted tests define a series of events. Scripted tests may make assumptions about ordering (e.g., create content in one test, use it in another).

Random tests are built mostly with actions. The "random.actions" module holds random test logic in classes; each "action_" method is an entry point for a random action.

The tests folder is organized into:

    dev     - Sandboxes for developing new tests
    random  - Random tests
    smoke   - Scripted tests for executing smoke tests
    ...     - Other test groupings as needed

# Running Tests

'testing/e2e/tests/smoke/basic.py' is hard-coded as the default for fab system test commands. Other system tests are run with dotted name of the file under 'tests':

    Run all 'test_xyz' methods in tests/smoke/content.py:

        fab test-local --test=smoke.content

    Only run 'test_1' in tests/dev/newtests.py:

        fab test-local -t=dev.newtests.test_1
