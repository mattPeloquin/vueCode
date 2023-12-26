#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Create launch templates necessary for ASGs
#

resource "aws_launch_template" "launch_templates" {
    for_each = var.profiles
        name = each.key
        image_id = var.ami
        instance_type = each.value.main_instance
    }
