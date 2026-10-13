import csv
import os
import statistics

def mtu_authorise_time(authorise_timeset,exclude_first=False):
    if exclude_first:
        print("(Excluding first test)")

    print(f"MTU authorise time cost")
    timeset={ 
        "make_message" : 0,
        "total_auth_time": 0,
        "share_collect_time" : 0,
        "key_construction" : 0,
        "message_signature_time" : 0,
        "zeroise_time": 0,
        "auth_time": 0,
        "share_cost" : 0,
        "send_message" : 0,
        "total_time": 0,
        "min": 0,
        "max": 0,
        "dev":0,
        "median":0,
             }

    first_time=None
    timeseries = []
    for trial in authorise_timeset[exclude_first==True:]:
        timeset["make_message"] += trial["make_message"]

        cost = trial["send_message_set"]
        timeset["auth_time"] += cost["auth_time"]
        timeset["zeroise_time"] += cost["zeroise_time"]
        timeset["total_auth_time"] += cost["total_auth_time"]
        timeset["share_collect_time"] += cost["share_collection"]
        timeset["key_construction"] += cost["key_construction"]
        timeset["message_signature_time"] += cost["message_signature_time"]
        timeset["share_cost"] += cost["share_cost_total"]
        timeset["send_message"] += cost["send_message"]

        timeset["total_time"] += trial["total_time"]
        if first_time is None: first_time = timeset["total_time"] * 1000
        timeseries.append(trial["total_time"] * 1000)
    
    cnt = len(authorise_timeset) - int(exclude_first==True)
    for cost in timeset:
        timeset[cost] = (timeset[cost] / cnt) * 1000

    
    if exclude_first== False:
        timeset["first_time"] = first_time
        print(f"first trial time cost: {first_time} ms")

    timeset["min"], timeset["max"],timeset["dev"],timeset["median"] = get_stat_values(timeseries,exclude_first)

    print(f"avg time to make message: {timeset["make_message"]} ms")
    print(f"avg time to send_message: {timeset["send_message"]} ms")
    print(f"avg time to authorise message: {timeset["total_auth_time"]} ms")
    print(f" --- avg time to collect shares: {timeset["share_collect_time"]} ms")
    print(f" --- avg time to construct key: {timeset["key_construction"]} ms")
    print(f" --- avg time to sign message: {timeset["message_signature_time"]} ms")
    print(f" --- avg time to zeroise key: {timeset["zeroise_time"]} ms")
    print(f" --- avg time to connect authorisation: {timeset["auth_time"]} ms")
    print(f"avg total time: {timeset["total_time"]} ms\n")
    print(f"lowest time: {timeset["min"]} ms, ")
    print(f"highest time: {timeset["max"]} ms, ")
    print(f"deviation: {timeset["dev"]}, ")

    return timeset

def get_stat_values(timeseries,exclude_first=False):
    times = sorted(timeseries[exclude_first:])
    dev = statistics.stdev(times) if len(times) > 1 else 0.0
    median = statistics.median(times)
    
    return times[0],times[max(0,len(times)-1)],dev,median


def mtu_test_evaluation_results(timeset,exclude_first=False):
    if exclude_first:
        print("Excluding first test:")

    results = {}
    print(f"MTU Evaluation Test results:")
    for res in timeset:
        avg_time = 0
        correct_authorised_rate = 0
        register_value_change_rate = 0

        timeseries = []
        for trial in timeset[res][exclude_first==True:]:
            avg_time += trial["time"]
            timeseries.append(trial["time"]*1000)
            correct_authorised_rate += trial["correct_result"]==True
            register_value_change_rate += trial["value_change_correct"]==True

        cnt = len(timeset[res]) - int(exclude_first==True)
        avg_time = avg_time/cnt * 1000
        correct_authorised_rate = correct_authorised_rate/cnt
        register_value_change_rate = register_value_change_rate/cnt

        min,max,dev,median = get_stat_values(timeseries,exclude_first)

        print(f"{res} (cnt: {cnt}): avg_time={avg_time} ms, min_time={min} ms, max_time={max} ms, median_time={median} ms, deviation={dev},correct_authorised_rate={correct_authorised_rate*100}%, correct_register_value_change={register_value_change_rate*100}%",flush=True)
        results[res] = {
                "cnt": cnt,
                "avg_time": avg_time,
                "min_time": min,
                "max_time": max,
                "median_time": median,
                "deviation": dev,
                "correct_authorised_rate": correct_authorised_rate,
                "correct_register_value_change": register_value_change_rate
                }

    print()
    return results

def control_results(res,exclude_first=False):
    if exclude_first:
        print("Excluding first test:")

    print(f"MTU Evaluation Control Test results:")

    avg_time = 0
    avg_send_msg_time = 0
    correct_authorised_rate = 0
    register_value_change_rate = 0

    first_time = None
    timeseries = []
    for trial in res[exclude_first==True:]:
        avg_time += trial["time"]
        if first_time is None: first_time = avg_time
        timeseries.append(trial["time"] *1000)

        avg_send_msg_time += trial["time_send_message"]
        correct_authorised_rate += trial["correct_result"]==True
        register_value_change_rate += trial["value_change_correct"]==True


    cnt = len(res) - int(exclude_first==True)

    avg_time = avg_time/cnt * 1000
    avg_send_msg_time = avg_send_msg_time/cnt * 1000
    first_time = first_time * 1000
    correct_authorised_rate = correct_authorised_rate/cnt 
    register_value_change_rate = register_value_change_rate/cnt

    max, min, dev, median = get_stat_values(timeseries,exclude_first)

    print(f"(cnt: {cnt}): avg_time={avg_time} ms, avg_send_msg_time={avg_send_msg_time} ms, min_time={min} ms, max_time={max} ms, median_time={median} ms, deviation={dev}, correct_authorised_rate={correct_authorised_rate*100}%, correct_register_value_change={register_value_change_rate*100}%",flush=True)

    results = {
            "cnt": cnt,
            "avg_time": avg_time,
            "avg_send_msg_time": avg_send_msg_time,
            "min_time": min,
            "max_time": max,
            "median_time": median,
            "deviation": dev,
            "first_time": first_time,
            "correct_authorised_rate": correct_authorised_rate,
            "correct_register_value_change": register_value_change_rate
            }

    print()
    return results

def export_csv(stage_avgs, results_summary,k,n,name, output_dir="/app/eval/"):
    os.makedirs(output_dir,exist_ok=True)
    filename = os.path.join(output_dir,name)

    with open(filename, "w", newline="") as f:
        writer  = csv.writer(f)
        writer.writerow([f"--- stage timing averages (ms) (k,n)=({k},{n}) ---"])
        writer.writerow(["stage", "avg_ms"])
        for stage, val in stage_avgs.items():
            writer.writerow([stage, val])

        writer.writerow([])
        writer.writerow([f"--- scenario results (k,n)=({k},{n})---"])
        writer.writerow(["scenario", "count", "avg_time_ms", "correct_authorised_rate_%", "register_value_change_rate_%"])
        for scenario, val in results_summary.items():
            writer.writerow([scenario, val["cnt"], val["avg_time"], val["correct_authorised_rate"], val["correct_register_value_change"]])

    print(f"wrote {filename}")

def export_control_csv(control_res,name, output_dir="/app/eval/"):
    os.makedirs(output_dir,exist_ok=True)
    filename = os.path.join(output_dir,name)

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([f"--- control timing results ---"])
        writer.writerow(["cnt", "avg_time" ,"avg_send_msg_time", "first_time","correct_authorised_rate_%", "correct_register_value_change_%"])
        print(f"control_res: {control_res}", flush=True)
        writer.writerow([control_res["cnt"],control_res["avg_time"],control_res["avg_send_msg_time"],control_res["first_time"],control_res["correct_authorised_rate"],control_res["correct_register_value_change"]])

    print(f"wrote {filename}")


def mtu_test_run(authorise_timeset,evaluation_results,k,n):
    authorise = mtu_authorise_time(authorise_timeset)
    evaluation = mtu_test_evaluation_results(evaluation_results)
    export_csv(authorise,evaluation,k,n,f"mtu_eval_(k,n)=({k},{n}).csv")

    #excluding first
    authorise=mtu_authorise_time(authorise_timeset,exclude_first=True)
    evaluation=mtu_test_evaluation_results(evaluation_results,exclude_first=True)
    export_csv(authorise,evaluation,k,n,f"mtu_eval_(k,n)=({k},{n}).csv","/app/eval/exclude_first")

def control_test_run(res,):
    results = control_results(res)
    print(f"resutls: {results}", flush=True)
    export_control_csv(results,f"control_mtu_eval.csv")

    #excluding first
    results = control_results(res,exclude_first=True)
    export_control_csv(results,f"control_mtu_eval.csv","/app/eval/exclude_first")
