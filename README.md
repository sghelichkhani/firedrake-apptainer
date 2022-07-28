# Firedrake Apptainer

This is a set of scripts and build definition files for building
[Firedrake] as an [Apptainer] container. The containers are composed
in layers, to avoid the need to completely rebuild the entire image
for any changes. It starts by building a base image containing OpenMPI
(for compatibility with the [Apptainer MPI methods]), and the rest of
the build dependencies required for Firedrake, including the [Intel
MKL] as the BLAS implementation. For ease of compatibility with the
Bind MPI model, this is based on a Docker image that's close to the
target operating system. The next layer is simply the base Firedrake
build itself, which can use a vanilla build, or a cached/customisable
build script. Finally, Firedrake, and optionally OpenMPI and MKL are
packaged into a fresh image without the full suite of build
dependencies. Particularly in the case where host libraries are bound
into the container, this gives a smaller image that is more flexible.

[Firedrake]: https://firedrakeproject.org/
[Apptainer]: https://apptainer.org/
[Apptainer MPI methods]: https://apptainer.org/docs/user/main/mpi.html
[Intel MKL]: https://www.intel.com/content/www/us/en/developer/tools/oneapi/onemkl.html


## The Firedrake build

With all the build dependencies in place, Firedrake can be built with
the unmodified upstream `firedrake-install` script. To update this
container, another layer can be composed, where the `firedrake-update`
script is run, which avoids re-downloading all the dependencies. As an
alternative to this approach, particularly during development it may
be the case that the base install is required several times. To avoid
repeated clones of the full dependency set, a script is provided to
perform these clones on the build system, along with a modified build
script that makes use of these (which are bound into the container
during build time).
