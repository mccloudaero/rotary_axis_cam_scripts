# Write dict
def write_dict(outfile, dict):
    for k, v in dict.items():
        outfile.write("    '"+str(k)+"'"+':')
        if type(v) is str:
            outfile.write("'"+v+"'"+',')
        else:
            outfile.write(str(v)+',')
        outfile.write('\n')
    outfile.write('}\n')
 
    return
