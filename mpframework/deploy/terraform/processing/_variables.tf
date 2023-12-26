#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Input variables for setting up servers
#

variable "profiles" {
    description = "An ASG and ELB target group is created for each key"
    default = {
        profile_name1 = {
            main_instance = "t3.micro",
            spot_instances = [],
            min_size = 1,
            max_size = 2,
            desired_size = 1,
            },
        profile_name2 = {},
        }
    }

variable "ami" {
    description = "The AMI to use with ASG launch templates"
    default = ""
    }
