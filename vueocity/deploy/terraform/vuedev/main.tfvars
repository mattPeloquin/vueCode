#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Config data for vuedev stack
#

ami = "ami-019360e0236d9f33d"

profiles = {
    dev = {
        main_instance = "t3.micro",
        min_size = 1,
        max_size = 2,
        },
    }
