# MPF Script loading

Uses django-compressor with production files to:

    - Combine files into fewer downloads for production
    - Invalidate files in browser and cloudfront caches
    - Compress and obfuscate scripts.
    - When compression is on, compression occurs at BUILD time, so...

VALUES THAT CHANGE AT RUNTIME CANNOT BE PART OF A COMPRESS BLOCK

Defer is used on scripts for debug loading where compression is not
used (compress only looks at first item for extra attributes).

FILES WITH COMPRESSION NEED TO BE SAVED WITH UNIX LINE TERMINATIONS
Otherwise the django-compressor hash for the scripts doesn't match
between offline build and the dev web serving.
