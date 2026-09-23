# CPU Node image-assembly workflow

1. Build a wheel or immutable release bundle from the accepted source. Record
   filename, version, source revision/archive digest and SHA-256.
2. Select the last accepted immutable image as the Node base unless the base
   stack intentionally changes. Query current resources and select a CPU Node;
   do not allocate a GPU Node for image assembly.
3. With explicit authority, create one minimally sized, short-lived CPU Node
   with an automatic shutdown deadline. Persist its request ID and Node ID.
   If creation returns a definite failure, stop and report it immediately. Do
   not retry, choose another Node, or hide the failure. If the outcome is
   unknown, query only the same request or Node identity and then report.
4. Upload the artifact through the authenticated Bohrium CLI to a project share
   path, for example:

   ```bash
   bohr file upload ./PACKAGE.whl \
     share/APP/VERSION/PACKAGE.whl --project-id PROJECT_ID
   ```

   Use the existing CLI profile. Do not create an SSH identity, temporary key,
   AccessKey or custom credential path, and do not use `scp` as the transfer
   mechanism.
5. Connect with the supported `bohr node connect` path. Read the artifact from
   `/share/APP/VERSION/PACKAGE.whl`, verify its SHA-256, then copy or install it
   into `/opt/app` or another ordinary image directory. `/share`, `/personal`
   and `/bohr` are transfer mounts and must not be runtime dependencies.
6. Perform construction checks only: confirm the intended interpreter, install
   destination, artifact digest, entry path and declared package versions. Do
   not run the complete scientific, adapter or resource test matrix on the
   mutable Node and do not treat these checks as runtime acceptance.
7. Remove repositories, VCS metadata, uploaded copies outside `share/`, tests,
   private data, logs, caches, temporary results, HAR files, credentials and
   shell history that must not enter the snapshot. Confirm required runtime
   files remain under ordinary image paths.
8. Confirm the requested new tag does not exist. Use a tested wrapper that
   delegates authentication to `bohr`, defaults to dry-run and refuses unsafe
   targets. Never replay HAR headers, cookies or browser requests.
9. After explicit snapshot authority, persist the accepted request and returned
   image identity. Monitor the same image; do not submit a duplicate on timeout.
10. Verify the image reaches the platform's documented ready state. Then run
    runtime acceptance from that immutable image as described in
    [image-and-app-acceptance.md](image-and-app-acceptance.md).
11. Query the source Node and stop it only when authorized if still running; do
    not assume the automatic shutdown completed.

Project-specific GPU, model, license or scientific tests remain mandatory on
the immutable image even though they are intentionally omitted from the CPU
assembly Node.
