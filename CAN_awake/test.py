import re
def get_circle_time(dict_config):
    times=[]
    for key in dict_config.keys():
        temp_times=re.findall("(\d+\.?\d*):(\d+\.?\d*):?(\d+\.?\d*)?",key)
        for i in range(len(temp_times)):
            temp_times[i]=list(temp_times[i])
            for j in range(len(temp_times[i])):
                if j!=2:
                    temp_times[i][j]=float(temp_times[i][j])*60
                else:
                    if temp_times[i][j]!="":
                        temp_times[i][j]=float(temp_times[i][j])
                    else:
                        temp_times[i][j]=13.5
        times+=temp_times*dict_config[key]
    return times


dict_config={
    "0:60,20:32": 10,
    "0:49:14,5:1": 51,
    }
print(get_circle_time(dict_config))
