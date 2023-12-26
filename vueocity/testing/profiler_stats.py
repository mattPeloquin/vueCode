import sys
import pstats

# Load either data for all threads, or only for one if filtered

p = pstats.Stats("ProfilerOutput")
#p.add(PROFILE_FILE + "Out")

filter = ''
if len(sys.argv) > 1:
    filter = sys.argv[1]

#p.strip_dirs()

p.sort_stats('cumulative')
p.print_stats(32, filter)


# Display output for stats, callers, callees
p.sort_stats('time')
p.print_stats(16, filter)
p.print_callers(4, filter)
p.print_callees(4, filter)
