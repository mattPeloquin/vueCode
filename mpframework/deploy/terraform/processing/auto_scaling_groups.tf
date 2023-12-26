#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Create the ASGs for each profile
#

resource "aws_autoscaling_group" "asgs" {

    # Create new groups before destorying old ones
    lifecycle {
        create_before_destroy = true
        }

    for_each = var.profiles

        # These are required options
        name = each.key
        launch_template {
            id      = aws_launch_template.launch_templates[ each.key ].id
            version = "$Latest"
            }
        min_size = each.value.min_size
        max_size = each.value.max_size
        availability_zones = data.aws_availability_zones.available_zones.names
    }

data "aws_availability_zones" "available_zones" {
    state = "available"
    }
