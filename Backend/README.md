# BookBridge Backend Environment

This backend folder provides everything needed for a local Python environment that can:

- run Apache Spark (via PySpark)
- open JupyterLab notebooks backed by Spark
- interact with Google Cloud Storage (GCS)
- submit PySpark jobs to an existing Dataproc cluster

> **Prerequisites**
>
> - Python 3.9+ (matching the version used by the Dataproc cluster)
> - Java 11+ (required by Spark)
> - `gcloud` CLI configured for the target GCP project
> - Access to a Dataproc cluster and a GCS bucket for staging jobs

## 1. Create the virtual environment

```bash
cd Backend
./scripts/init_venv.sh
source .venv/bin/activate
```

This installs all dependencies listed in `requirements.txt` (PySpark, JupyterLab, Google Cloud SDK bindings) and registers a `BookBridge Backend` kernel for Jupyter.

## 2. Configure credentials and project context

1. Copy `.env.example` to `.env` and fill in the values for your project (project ID, region, cluster name, staging bucket, etc.).
2. Authenticate with Google Cloud:
   ```bash
   gcloud auth login
   gcloud config set project <PROJECT_ID>
   # Optional: create application default credentials for client libraries
   gcloud auth application-default login
   ```
3. If you rely on a service-account JSON key instead, set `GOOGLE_APPLICATION_CREDENTIALS` in your `.env`.

The Python utilities call `python-dotenv`, so any values stored in `.env` are picked up automatically.

## 3. Launch JupyterLab with PySpark

```bash
./scripts/start_jupyter.sh        # defaults to port 8888
PORT=8890 ./scripts/start_jupyter.sh  # override port if needed
```

This script activates the virtual environment, wires `pyspark` to start JupyterLab, and automatically adds the GCS connector so notebooks can read/write `gs://` paths. You can manage notebooks inside `Backend/notebooks/`.

## 4. Run the PySpark REPL locally

```bash
./scripts/run_pyspark.sh
```

The REPL includes the same GCS connector configuration as the Jupyter setup. Pass any extra Spark flags after the script (e.g., `./scripts/run_pyspark.sh --conf spark.executor.instances=2`).

## 5. Submit a PySpark job to Dataproc

1. Upload your PySpark driver file to GCS (for example using `gsutil cp app.py gs://my-bucket/jobs/app.py`).
2. Update `.env` with `PYSPARK_SUBMIT_FILE` pointing to that `gs://` path.
3. Submit the job:
   ```bash
   source .venv/bin/activate
   python -m src.dataproc_submit --arg input=gs://... --arg output=gs://...
   # or override values ad-hoc
   python -m src.dataproc_submit --project-id my-project --region us-central1 \
       --cluster analytics-cluster --pyspark-file gs://bucket/jobs/app.py
   ```

The helper wraps `google-cloud-dataproc`'s `JobControllerClient` and only requires your cluster/project info plus the PySpark entrypoint location.

## 6. Work with Google Cloud Storage programmatically

`src/gcs_io.py` shows how to interact with GCS through the `google-cloud-storage` client. Example usage:

```bash
source .venv/bin/activate
python -m src.gcs_io
```

It will upload the backend README into the bucket specified by `GCS_STAGING_BUCKET`.

## Directory layout

```
Backend/
├── .env.example                # Template for local secrets/config
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── config/
├── notebooks/
├── scripts/
│   ├── init_venv.sh            # Creates .venv and installs deps
│   ├── run_pyspark.sh          # Starts PySpark REPL with GCS support
│   └── start_jupyter.sh        # Launches JupyterLab via PySpark
└── src/
    ├── __init__.py
    ├── dataproc_submit.py     # Submitter for Dataproc PySpark jobs
    └── gcs_io.py              # Simple GCS helper utilities
```

## Troubleshooting tips

- **Java errors when starting Spark**: ensure `JAVA_HOME` targets a Java 11+ installation (`/usr/libexec/java_home -v 11`).
- **Google authentication errors**: either run `gcloud auth application-default login` or set `GOOGLE_APPLICATION_CREDENTIALS` to a valid service-account JSON file.
- **Jupyter cannot find kernel**: rerun `./scripts/init_venv.sh` after upgrading dependencies so the kernel spec stays in sync.
- **Dataproc job stuck in `PENDING`**: confirm the cluster is running and that the staging bucket is in the same region as the cluster.
