provider "google" {
  credentials = "${file("${var.credential_path}")}"
  project     = "${var.project_name}"
  region      = "us-east1"
}


resource "template_file" "salt_bootstrap_dataSubscriber" {
    count    = "${var.dataSubscriber_count}"
    template = "${file("salt_bootstrap_dataSubscriber.tpl")}"

    vars {
        hostname = "${lookup(var.dataSubscriber_hostnames, count.index)}"
        local_ip = "${lookup(var.dataSubscriber_ips, count.index)}"
    }
}


resource "google_compute_instance" "dataSubscriber" {

  count = "${var.dataSubscriber_count}" 

  name         = "${lookup(var.dataSubscriber_names, count.index)}"
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

  metadata_startup_script = "${element(template_file.salt_bootstrap_dataSubscriber.*.rendered, count.index)}"

}