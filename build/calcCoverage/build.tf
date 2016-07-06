provider "google" {
  credentials = "${file("${var.credential_path}")}"
  project     = "${var.project_name}"
  region      = "us-central1"
}


resource "template_file" "salt_bootstrap_coverage" {
    count    = "${var.coverage_count}"
    template = "${file("salt_bootstrap_coverage.tpl")}"

    vars {
        hostname = "${lookup(var.coverage_hostnames, count.index)}"
        local_ip = "${lookup(var.coverage_ips, count.index)}"
        numInstances = "${lookup(var.numInstances, count.index)}"
        haProxyIP = "${var.haProxyIP}"
        quidID = "${var.qid}"
        tableName = "${var.tableName}"
        startTime = "${var.startTime}"
        numDays = "${var.numDays}"
        numIDs = "${var.numIDs}"
        startID = "${var.startID}"
    }
}


resource "google_compute_instance" "coverage" {

  count = "${var.coverage_count}" 

  name         = "${lookup(var.coverage_names, count.index)}"
  machine_type = "n1-standard-1"
  zone         = "us-central1-b"


  disk {
    image = "${var.image}"
    size = 40
  }

  network_interface {
    network = "riakstack01"
    access_config {
        // Ephemermal IP
    }
  }

  metadata_startup_script = "${element(template_file.salt_bootstrap_coverage.*.rendered, count.index)}"

}
