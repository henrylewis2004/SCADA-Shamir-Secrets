import csv
import os

def mtu_authorise_time(authorise_timeset,exclude_first=False):
    if exclude_first:
        print("(Excluding first test)")

    print(f"MTU authorise time cost")
    timeset={ 
        "make_message" : 0,
        "total_auth_time": 0,
        "auth_time": 0,
        "zeroise_time": 0,
        "share_collect_time" : 0,
        "key_construction" : 0,
        "message_signature_time" : 0,
        "share_cost" : 0,
        "send_message" : 0,
        "total_time": 0
             }

    for trial in authorise_timeset[exclude_first==True:]:
        timeset["make_message"] += trial.get("make_message",0)

        cost = trial["send_message_set"]
        timeset["auth_time"] += cost.get("auth_time",0)
        timeset["zeroise_time"] += cost.get("zeroise_time",0)
        timeset["total_auth_time"] += cost.get("total_auth_time",0)
        timeset["share_collect_time"] += cost.get("share_collection",0)
        timeset["key_construction"] += cost.get("key_construction",0)
        timeset["message_signature_time"] += cost.get("message_signature_time",0)
        timeset["share_cost"] += cost.get("share_cost_total",0)
        timeset["send_message"] += cost.get("send_message",0)

        timeset["total_time"] += trial.get("total_time",0)
    
    cnt = len(authorise_timeset) - int(exclude_first==True)
    for cost in timeset:
        timeset[cost] = (timeset[cost] / cnt) * 1000

    print(f"avg time to make message: {timeset["make_message"]} ms")
    print(f"avg time to send_message: {timeset["send_message"]} ms")
    print(f"avg time to authorise message: {timeset["total_auth_time"]} ms")
    print(f" --- avg time to collect shares: {timeset["share_collect_time"]} ms")
    print(f" --- avg time to construct key: {timeset["key_construction"]} ms")
    print(f" --- avg time to sign message: {timeset["message_signature_time"]} ms")
    print(f" --- avg time to zeroise key: {timeset["zeroise_time"]} ms")
    print(f" --- avg time to connect authorisation: {timeset["auth_time"]} ms")
    print(f"avg total time: {timeset["total_time"]} ms\n")

    return timeset

def mtu_test_evaluation_results(timeset,exclude_first=False):
    if exclude_first:
        print("Excluding first test:")

    results = {}
    print(f"MTU Evaluation Test results:")
    for res in timeset:
        avg_time = 0
        correct_authorised_rate = 0
        register_value_change_rate = 0

        for trial in timeset[res][exclude_first==True:]:
            avg_time += trial.get("time",0)
            correct_authorised_rate += trial.get("correct_result",False)==True
            register_value_change_rate += trial.get("value_change_correct",False)==True

        cnt = len(timeset[res]) - int(exclude_first==True)
        avg_time = avg_time/cnt * 1000
        correct_authorised_rate = correct_authorised_rate/cnt
        register_value_change_rate = register_value_change_rate/cnt

        print(f"{res} (cnt: {cnt}): avg_time={avg_time} ms, correct_authorised_rate={correct_authorised_rate*100}%, correct_register_value_change={register_value_change_rate*100}%",flush=True)
        results[res] = {"cnt": cnt, "avg_time": avg_time, "correct_authorised_rate": correct_authorised_rate, "correct_register_value_change": register_value_change_rate}

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

    for trial in res[exclude_first==True:]:
        avg_time += trial.get("time",0)
        avg_send_msg_time = trial.get("time_send_message",0)
        correct_authorised_rate += trial.get("correct_result",False)==True
        register_value_change_rate += trial.get("value_change_correct",False)==True


    cnt = len(res) - int(exclude_first==True)

    avg_time = avg_time/cnt * 1000
    avg_send_msg_time = avg_send_msg_time/cnt * 1000
    correct_authorised_rate = correct_authorised_rate/cnt 
    register_value_change_rate = register_value_change_rate/cnt

    print(f"(cnt: {cnt}): avg_time={avg_time} ms, avg_send_msg_time={avg_send_msg_time} ms, correct_authorised_rate={correct_authorised_rate*100}%, correct_register_value_change={register_value_change_rate*100}%",flush=True)

    results = {"cnt": cnt, "avg_time": avg_time, "avg_send_msg_time": avg_send_msg_time,"correct_authorised_rate": correct_authorised_rate, "correct_register_value_change": register_value_change_rate}

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
            writer.writerow([stage, val * 1000])

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
        writer.writerow(["cnt", "avg_time" ,"avg_send_msg_time","correct_authorised_rate_%", "correct_register_value_change_%"])
        print(f"control_res: {control_res}", flush=True)
        writer.writerow([control_res["cnt"],control_res["avg_time"],control_res["avg_send_msg_time"],control_res["correct_authorised_rate"],control_res["correct_register_value_change"]])

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
