#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Config data for production stack
#

ami = "ami-019360e0236d9f33d"

profiles = {
    prod = {
        main_instance = "t3.micro",
        min_size = 1,
        max_size = 2,
        },
    prod-boh = {
        main_instance = "t3.micro",
        min_size = 1,
        max_size = 2,
        },
    prod-ft = {
        main_instance = "t3.micro",
        min_size = 1,
        max_size = 2,
        },
    prod-osk = {
        main_instance = "t3.micro",
        min_size = 1,
        max_size = 2,
        },
    prod-mpd = {
        main_instance = "t3.micro",
        min_size = 1,
        max_size = 2,
        },
    }
