# S3Direct build

S3Direct wraps EvaporateJS, but a key opption for S3 accelerate isn't exposed, so modifications to the library were needed.

Due to the packaging of S3Direct, there was no easy way to monkey-patch the compiled code or include the original code instead.

Thus the index.js file here is the modified source, and the files under dist are built in the npm environment by manually moving the updated file.
