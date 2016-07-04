provider "google" {
  credentials = "${file("${var.credential_path}")}"
  project     = "${var.project_name}"
  region      = "us-east1"
}


resource "template_file" "salt_bootstrap_dataPublisher" {
    count    = "${var.dataPublisher_count}"
    template = "${file("salt_bootstrap_dataPublisher.tpl")}"

    vars {
        hostname = "${lookup(var.dataPublisher_hostnames, count.index)}"
        local_ip = "${lookup(var.dataPublisher_ips, count.index)}"
        start_id = "${lookup(var.startID, count.index)}"
    }
}


resource "google_compute_instance" "dataPublisher" {

  count = "${var.dataPublisher_count}" 

  name         = "${lookup(var.dataPublisher_names, count.index)}"
  machine_type = "n1-standard-1"
  zone         = "us-east1-d"


  disk {
    image = "${var.image}"
    size = 40
  }

  network_interface {
    network = "riak-network"
    access_config {
        // Ephemermal IP
    }
  }

  metadata_startup_script = "${element(template_file.salt_bootstrap_dataPublisher.*.rendered, count.index)}"

}
