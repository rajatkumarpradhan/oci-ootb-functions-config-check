# TEMPLATE ONLY - NOT plan/apply validated against a live tenancy.
# Built-in resources: OCI Functions application + function.
# Field names per the oracle/oci provider docs (oci_functions_application,
# oci_functions_function). Conventions shown: explicit timeout_in_seconds and
# memory_in_mbs (never the 30s / 128MB silent defaults), no secrets in config
# (use OCI Vault), image referenced from OCIR with a pinned tag.

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0"
    }
  }
}

variable "compartment_id" {
  type        = string
  description = "OCID of the compartment"
}

variable "subnet_id" {
  type        = string
  description = "OCID of the subnet the application's functions run in"
}

resource "oci_functions_application" "webshop" {
  compartment_id = var.compartment_id
  display_name   = "webshop"
  subnet_ids     = [var.subnet_id]
}

resource "oci_functions_function" "checkout" {
  application_id     = oci_functions_application.webshop.id
  display_name       = "checkout"
  memory_in_mbs      = 256 # explicit - never the 128MB silent default
  timeout_in_seconds = 60  # explicit - never the 30s silent default

  source_details {
    source_type = "CONTAINER_IMAGE"
    image       = "iad.ocir.io/tenancy/webshop/checkout:v1.4.3" # pinned tag
  }

  config = {
    LOG_LEVEL = "info" # no secrets here - read them from OCI Vault at runtime
  }
}
