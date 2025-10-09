# Models Directory

This directory stores downloaded HuggingFace models for vLLM.

## Structure

Models are cached in the HuggingFace Hub format:
```
models/
├── hub/
│   └── models--{org}--{model-name}/
│       ├── snapshots/
│       └── refs/
```

## Management

- **Download**: Use the frontend settings or API endpoint `/api/download-model`
- **Delete**: Remove model directories manually or use `/api/delete-model`
- **List**: Check `/api/models` or browse this directory

## Permissions

This directory is mounted into Docker containers and accessible from the host system.
You can manage models directly from your file system.
