import time

def mtu_test_run(results):
    #results = [{trial1},{trial2}...]
    
    print(f"MTU Evaluation Test results:")
    for res in results:
        avg_time = 0
        correct_authorised_rate = 0
        register_value_change_rate = 0

        for trial in results[res]:
            avg_time += trial["time"]
            correct_authorised_rate += trial["correct_result"]==True
            register_value_change_rate += trial["value_change_correct"]==True

        avg_time = avg_time/len(results[res])
        correct_authorised_rate = correct_authorised_rate/len(results[res])
        register_value_change_rate = register_value_change_rate/len(results[res])

        print(f"{res} (cnt: {len(results[res])}): avg_time={avg_time*1000} ms, correct_authorised_rate={correct_authorised_rate*100}%, correct_register_value_change={register_value_change_rate*100}%",flush=True)



