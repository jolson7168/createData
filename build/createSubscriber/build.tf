provider "google" {
  credentials = "${file("${var.credential_path}")}"
  project     = "${var.project_name}"
  region      = "us-central1"
}


resource "template_file" "salt_bootstrap_dataSubscriber" {
    count    = "${var.dataSubscriber_count}"
    template = "${file("salt_bootstrap_dataSubscriber.tpl")}"

    vars {
        hostname = "${lookup(var.dataSubscriber_hostnames, count.index)}"
        local_ip = "${lookup(var.dataSubscriber_ips, count.index)}"
        numInstances = "${lookup(var.numInstances, count.index)}"
        haProxyIP = "${var.haProxyIP}"
        rabbitIP = "${var.rabbitIP}"
        log01 = "${var.log01}"
        p01 = "${var.p01}"
        queueName = "${var.queueName}"
        tableName = "${var.tableName}"
    }
}

resource "google_compute_instance" "dataSubscriber" {

  count = "${var.dataSubscriber_count}" 

  name         = "${lookup(var.dataSubscriber_names, count.index)}"
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

  metadata_startup_script = "${element(template_file.salt_bootstrap_dataSubscriber.*.rendered, count.index)}"

}
