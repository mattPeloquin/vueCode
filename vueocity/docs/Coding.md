
MPF Coding
==========

# Revision Control

 - 1 Main dev trunk and 1 Main release trunk
 - Frequent, focused checkins (minutes, hours), avoid more than one item
 - Feature branches only when needed

# Third-party and open source code
  - Only permissive open source licenses are used
  - Commercial use is separated from open mpFramework base platform
  - Balance create from scratch vs. large/complex web of 3rd party dependencies
  - Prefer one broad solutions per category (Django, lodash) or narrow ones that fit the problem
  - Prefer external services over inclusion into the system
  - Prefer installing package/binary dependencies over including in code repo
  - All usage and dependencies are clearly identified and separated from MPF code
  - Avoid modifying included code

# Coding Standards

    1) Follow existing style in established code

    2) Next, follow Python, Django guidelines for all code (.py, .js, templates, scripts, config files, etc.)...

        http://www.python.org/dev/peps/pep-0008/
        https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

    3) ...with additions/modifications/clarifications below:

    - Follow existing folder structure and file conventions defined in ReadMe files
    - File structure for all file types (Python, JS, HTML, YAML) is Java-ish:
        Prefer smaller size and narrow focus but...
        ...but no rigid rules like 1 class per file
        For module imports, each item on a separate line
    - Standard header at top of ALL files except empty __init__ and 3rd party
    - JS code is slowly migrating to ES6 standards (unnecessary lodash can be converted)
    - JS and HTML style borrows from Python style for consistency:
        No semicolons in JS
        Use Python-style indentation

 ## Code comments

  - Don't repeat the code, focus on WHY the code exists
  - Focus on high-leverage DESIGN comments in file, class, and routine headers
  - Low-level details should be clear from code
  - CONSTRUCTION comments
      Are usually short unless explaining background for technology issue
      Do not comment items obvious to someone familiar with Python/Django/JS/HTML
  - NO AUTO DOC; comments consumed in-place -- code files ARE the documentation

## Logging

  - Use debug logging messages frequently and liberally
  - Use production messages to highlight operational visibility, security, and reliability
  - Logging statements can replace construction comments
  - Separate human-message logging from programmatic monitoring (see discussion in log module)
  - For verbose items, especially inside loops, use debug filtering options
  - Use "%" string replacement (vs. format) with logging module arguments

## Strings

  - Prefer format string replacement (vs. %) for all strings (except logging)
  - In Python and JS...
        Use double quotes for viewable text,
        single quotes for programmatic names,
        ...EXCEPT for HTML...
           prefer double quotes for HTML attributes, whether in templates or JS
  - In Python, triple-doubles for comments, triple-singles for programmatic content

## Django

  - Unless Forms are used in multiple places, embed forms with admin/view files
  - Prefer external JS files to embedding JS in template files
  - Prefer template comments to native html or JS comments in HTML template files

## SQL Code

There may be exceptions, but goal is to NOT HAVE ANY SQL CODE; all DB logic should be through Django ORM.
This includes SQL scripts run against DBs and embedded SQL.

