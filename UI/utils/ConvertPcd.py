import os
import numpy as np
import pandas as pd
import re
from io import StringIO
import time

def load_pcd_header(path):
    if not os.path.exists(path):
        print(f"pcd file {path} not exists!")
        return ""
    pcd_header=""
    with open(path,'rb') as f:
        while True:
            ln=f.readline().strip().decode()
            if not ln:
                break
            pcd_header+=ln+"\n"
            if re.search("^DATA",ln):
                break
    return pcd_header


def read_pcd(path):#return dataframe
    df = pd.DataFrame([],columns=[])
    if not os.path.exists(path):
        print(f"pcd file {path} not exists!")
        return df
    metadata={
        'FIELDS':False,
        'SIZE':False,
        'TYPE':False,
        'POINTS':False
    }
    ascii_flag=None
    with open(path,'rb') as f:
        while True:
            try:
                ln=f.readline().strip().decode()
            except:
                print("pcd file no header")
                return df
            if not ln:
                print("pcd file is empty or not header")
                return df
            ret=re.search("^([A-Z]+)\s(.+)$",ln)
            if ret:
                key,value=ret.group(1),ret.group(2).strip()
                if key=='FIELDS':
                    metadata['FIELDS']=value.split()
                elif key=='SIZE':
                    metadata['SIZE']=np.array(value.split(),dtype=np.uint8)
                elif key=='TYPE':
                    metadata['TYPE']=value.lower().split()
                elif key=='POINTS':
                    metadata['POINTS']=int(value)
                    if metadata['POINTS']==0:
                        print("pcd file points is 0!")
                        return df
                elif key == "DATA":
                    if "ascii"==value:
                        ascii_flag=True
                    elif "binary"==value:
                        ascii_flag=False
                    break
        for key in metadata:
            if isinstance(metadata[key],bool):
                print(f"{key} not in pcd file!")
                return df
        buff_length=(np.sum(metadata['SIZE'])*metadata['POINTS'])
        buff_length=buff_length.astype(np.uint64)
        dt_dict = {
                'names': metadata['FIELDS'],
                'formats': [f"{metadata['TYPE'][i]}{metadata['SIZE'][i]}" for i in range(len(metadata['TYPE']))],
            }
        dt_point=np.dtype(dt_dict)
        if ascii_flag==True:
            dt={}
            for name,d_type in zip(dt_dict["names"],dt_dict["formats"]):
                dt[name]=d_type
            res=f.read().decode()
            csv_data=StringIO(res)
            df=pd.read_csv(csv_data,header=None,sep=' ')
            if df.shape[1]!=len(metadata['FIELDS']):
                print("pcd file fields not match!")
                return pd.DataFrame([],columns=metadata['FIELDS'])
            df.columns=metadata['FIELDS']
            df=df.astype(dt)
            return df
        elif ascii_flag==False:
            res=f.read(buff_length)
            if len(res)==buff_length:
                data=np.frombuffer(res[:buff_length],dtype=dt_point)
                df=pd.DataFrame.from_records(data,columns=metadata['FIELDS'])
                return df
            else:
                print("pcd file not enough length!")
        return pd.DataFrame([],columns=metadata['FIELDS'])


    

def df2pcd(df, file_name, binary=False):
    if not isinstance(df,pd.DataFrame):
        if not isinstance(df[0],list) and not isinstance(df[0],np.ndarray):
            print(f"input data shape ({len(data)})")
            return
        if len(df[0]) == 3:
            columns = ["x","y","z"]
        elif len(df[0]) == 4:
            columns = ["x","y","z","label"]
        else:
            print(f"input data shape ({len(data)},{len(data[0])})")
            return
        df = pd.DataFrame(df,columns=columns)
    count = []
    type_dict={
        "int":"I",
        "uint":"U",
        "float":"F"
    }
    sizes=[]
    types=[]
    fields = []
    for col in df.columns:
        if str(df[col].dtype)=="object":
            if df[col].astype(str).str.match("^\d+\.?\d*$").all():
                sizes.append(8)
                types.append("F")
                fields.append(col)
                count.append("1")
            else:
                continue
        else:
            ret=re.search("^(.+?)(\d+)$",str(df[col].dtype))
            if not ret:
                print(f"Dataframe dtype fault, {col} dtype is {df[col].dtype}!")
                return
            sizes.append(int(max(int(ret.group(2))/8,2)))  
            types.append(type_dict[ret.group(1)])
            fields.append(col)
            count.append("1")
    df = df[fields]
    header=f'''# .PCD v.7 - Point Cloud Data file format
FIELDS {" ".join(fields)}
SIZE {" ".join(map(str,sizes))}
TYPE {" ".join(types)}
COUNT {" ".join(count)}
POINTS {df.shape[0]}
DATA ascii\n'''
    if not binary:
        data = df.to_numpy()
        header=header.replace("binary","ascii")
        with open(file_name,"w") as f:
            f.write(header)
            ret=re.search("TYPE\s(.+)",header)
            data_type=ret.group(1).split(" ")
            fmt=""
            for j in range(len(data[0])):
                if data_type[j]=="F":
                    fmt+="%f "
                else:
                    fmt+="%d "
            np.savetxt(f, data, fmt=fmt[:-1], delimiter=' ',newline='\n')
    else:
        dt=np.dtype({
            'names': fields,
            'formats': [f"{types[i].lower()}{sizes[i]}" for i in range(len(types))],
        })
        ndarray_data=df.to_records(index=False).astype(dt)
        header=header.replace("ascii","binary")
        with open(file_name,"wb") as f:
            f.write(header.encode())
            f.write(ndarray_data.tobytes())
    

def bag_fix(bag_file):
    bag_file_abs=os.path.abspath(bag_file)
    cmd = os.popen(f'rosbag reindex {bag_file_abs}')
    cmd.readlines()
    cmd = os.popen(f'rosbag fix {bag_file_abs} {bag_file_abs}')
    cmd.readlines()
    dir_path=os.path.dirname(bag_file_abs)
    file_name=os.path.basename(bag_file_abs)
    for file_ in os.listdir(dir_path):
        if re.search("\.orig\.bag$",file_):
            os.remove(os.path.join(dir_path,file_))


def read_bag(path):
    import rosbag
    import sensor_msgs.point_cloud2 as pc2
    from sensor_msgs.msg import PointField
    _DATATYPES={
        PointField.UINT8:["u1",np.uint8],
        PointField.UINT16:["u2",np.uint16],
        PointField.UINT32:["u4",np.uint32],
        PointField.INT8:["i1",np.int8],
        PointField.INT16:["i2",np.int16],
        PointField.INT32:["i4",np.int32],
        PointField.FLOAT32:["f4",np.float32],
        PointField.FLOAT64:["f8",np.float64]
    }
    try:
        bag = rosbag.Bag(path)
    except:
        bag_fix(path)
        bag = rosbag.Bag(path)
    info = bag.get_type_and_topic_info()
    topic = None
    for topic_temp in info.topics:
        if re.search("(point)",topic_temp):
            topic = topic_temp
            break
    if topic==None:
        print(f"bag file not has point topic!")
        return pd.DataFrame([])
    bag_data = bag.read_messages(topics=topic)
    frame_id=0
    array_data=None
    df_frame_id=np.array([])
    data_tuple=()
    for _, msg, _ in bag_data:
        
        # fields=[field.name for field in msg.fields]
        # df_temp=pd.DataFrame(pc2.read_points(msg),columns=fields)
        
        sum_size=0
        dt = {
            'names': [],
            'formats': [],
            'offsets': []
        }
        num_points = int(msg.row_step / msg.point_step)
        for field in msg.fields:
            dtype=_DATATYPES[field.datatype]
            field_size=int(dtype[0][1:])
            sum_size+=field.count*field_size
            dt["names"].append(field.name)
            dt["formats"].append(dtype[0])
            dt["offsets"].append(field.offset)
        dtypes=np.dtype(dt)
        msg_data = np.frombuffer(msg.data, dtype=np.uint8)
        reshaped_data = msg_data.reshape(-1, msg.point_step)
        reshaped_data = reshaped_data[:,:(field.offset+field_size)]
        data=reshaped_data.view(dtype=dtypes)
        data_tuple+=(np.squeeze(data),)
        df_frame_id=np.r_[df_frame_id,np.full(num_points,frame_id,dtype=np.uint32)]
        frame_id+=1
    array_data=np.r_[tuple(data_tuple)]
    df=pd.DataFrame(array_data)
    df["frame_id"]=df_frame_id.astype(np.uint32)
    return df


def binary2ascii(pcd_path,save_path):
    df=read_pcd(pcd_path)
    df2pcd(df,save_path,False)


def calc_frame(path):
    df=read_pcd(path)
    return df["frame_id"].unique().shape[0]

if __name__=='__main__':
    value = [[i*0.1,i*0.2,i*0.3,"a"] for i in range(1000)]
    df = pd.DataFrame(value,columns=["x","y","z","label"])
    df2pcd(df.iloc[:,:3],"1.pcd",True)
    df2pcd(df.iloc[:,:3],"2.pcd",False)