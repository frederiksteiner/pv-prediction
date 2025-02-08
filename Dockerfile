FROM python:3.12-slim-bookworm


# Set all required environment variables
ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  MPLCONFIGDIR="/tmp/.cache/matplotlib" \
  WORKDIR="/app" \
  HOME="${WORKDIR}/src" \
  POETRY_CONFIG_DIR="${WORKDIR}/.config" \
  PATH="${WORKDIR}/src/.local/bin:$PATH"


# Copy project files
WORKDIR ${WORKDIR}
COPY . ./


# System dependencies:
USER 0
RUN dnf upgrade -y && dnf install -y postgresql-libs nginx \
  # This is needed due to numpy error numpy.distutils.system_info.NotFoundError: No BLAS/LAPACK libraries found
  # See also https://stackoverflow.com/a/34457723
  atlas-devel gcc \
  && dnf remove -y http-core \
  && curl -sSL https://install.python-poetry.org | python3 - \
  && poetry env use 3.12 \
  # Create Matplotlib and Poetry config directories
  && mkdir -p ${MPLCONFIGDIR} ${POETRY_CONFIG_DIR} \
  # Assign root group permissions to directories
  && chgrp -R 0 ${MPLCONFIGDIR} ${POETRY_CONFIG_DIR} ${WORKDIR} ${HOME} \
  && chmod -R g=u ${MPLCONFIGDIR} ${POETRY_CONFIG_DIR} ${WORKDIR} ${HOME}
USER 1001


# Project installation:
# Upgrade pip
RUN pip install --upgrade pip \
  && poetry config --local virtualenvs.create false \
  # Install Poetry
  && poetry install --only main --no-interaction --no-ansi


# Final group permissions for adapted files
USER 0
# Reassign group permissions due to adapted files
RUN chgrp -R 0 ${POETRY_CONFIG_DIR} ${WORKDIR} \
  && chmod -R g=u ${POETRY_CONFIG_DIR} ${WORKDIR}
USER 1001
