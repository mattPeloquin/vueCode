#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Config data for vuecam test setups
#

ami = "ami-019360e0236d9f33d"

profiles = {
    prod-mpd = {
        main_instance = "t3.micro",
        min_size = 1,
        max_size = 2,
        },
    }
