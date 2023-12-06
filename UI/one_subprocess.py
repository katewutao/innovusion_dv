from log_statistic import Log_statistic
import argparse
import os
import pandas as pd
from utils.excel_format import ExcelFormat


def main(args):
    ls = Log_statistic(pcs_path=args.pcs_path, fw_path=args.fw_path, client_log_path=args.client_path)
    save_folder = os.path.dirname(args.save_path)
    if not os.path.exists(save_folder):
        try:
            os.makedirs(save_folder)
        except:
            pass
    sum_shape = sum([ls.dict_df[key].shape[0] for key in ls.dict_df.keys()])
    if sum_shape == 0:
        return
    writer = pd.ExcelWriter(args.save_path)
    for key in ls.dict_df.keys():
        if ls.dict_df[key].shape[0] == 0:
            continue
        ls.dict_df[key].to_excel(writer, sheet_name=key, index=False)
    writer.close()
    ExcelFormat(args.save_path).format()


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--fw-path',"-fp", type=str, default=None, help='log file path')
    parser.add_argument('--pcs-path',"-pp",type=str, default=None, help='log file path')
    parser.add_argument('--client-path', "-cp" ,type=str, default=None, help='log file path')
    parser.add_argument('--save-path', "-sp" ,type=str, default=None, help='save file path')
    args = parser.parse_args()
    main(args)