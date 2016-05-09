
type file;

# 64 ... 2048
int N = toInt(arg("N", "64"));

# -----------------------------------------------------------------------------
#
# Stage 1
#
app (file output_1_1_i,
     file output_1_2_i,
     file output_1_3_i) stage_1 (int  i,
                                 file input_shared_1_1, 
                                 file input_shared_1_2, 
                                 file input_shared_1_3,
                                 file input_shared_1_4,
                                 file input_shared_1_5)
{
    stage_1_exe i filename(input_shared_1_1) 
                  filename(input_shared_1_2) 
                  filename(input_shared_1_3) 
                  filename(input_shared_1_4) 
                  filename(input_shared_1_5);
}

file input_shared_1_1 <"input_shared_1_1.txt">;
file input_shared_1_2 <"input_shared_1_2.txt">;
file input_shared_1_3 <"input_shared_1_3.txt">;
file input_shared_1_4 <"input_shared_1_4.txt">;
file input_shared_1_5 <"input_shared_1_5.txt">;

file output_1_1[];
file output_1_2[];
file output_1_3[];

foreach i in [1:N] {
    file output_1_1_i <single_file_mapper; file=strcat("output_1_1_",i,".txt")>;
    file output_1_2_i <single_file_mapper; file=strcat("output_1_2_",i,".txt")>;
    file output_1_3_i <single_file_mapper; file=strcat("output_1_3_",i,".txt")>;

    (output_1_1_i, 
     output_1_2_i, 
     output_1_3_i) = stage_1(i, 
                             input_shared_1_1, 
                             input_shared_1_2, 
                             input_shared_1_3,
                             input_shared_1_4,
                             input_shared_1_5);

    output_1_1[i] = output_1_1_i;
    output_1_2[i] = output_1_2_i;
    output_1_3[i] = output_1_3_i;
}


# -----------------------------------------------------------------------------
#
# Stage 2
#
app (file output_2_1_i,
     file output_2_2_i,
     file output_2_3_i,
     file output_2_4_i) stage_2 (int  i, 
                                 file input_shared_1_3, 
                                 file input_shared_1_4,
                                 file output_1_1_i)
{
    stage_2_exe i filename(input_shared_1_3) 
                  filename(input_shared_1_4) 
                  filename(output_1_1_i);
}

file output_2_1[];
file output_2_2[];
file output_2_3[];
file output_2_4[];

foreach i in [1:N] {

    file output_2_1_i <single_file_mapper; file=strcat("output_2_1_",i,".txt")>;
    file output_2_2_i <single_file_mapper; file=strcat("output_2_2_",i,".txt")>;
    file output_2_3_i <single_file_mapper; file=strcat("output_2_3_",i,".txt")>;
    file output_2_4_i <single_file_mapper; file=strcat("output_2_4_",i,".txt")>;
    
    (output_2_1_i, 
     output_2_2_i, 
     output_2_3_i, 
     output_2_4_i) = stage_2(i,
                             input_shared_1_3,
                             input_shared_1_4,
                             output_1_1[i]);

    output_2_1[i] = output_2_1_i;
    output_2_2[i] = output_2_2_i;
    output_2_3[i] = output_2_3_i;
    output_2_4[i] = output_2_4_i;
}


# -----------------------------------------------------------------------------
#
# Stage 3
#
app (file[] output_3_1) stage_3 (file   input_shared_1_3, 
                                 file[] output_2_2)
{
    # N cores
    stage_3_exe filename(input_shared_1_3) 
                @output_2_2;
}

string[] output_3_1_s;
foreach i in [1:N] {
    output_3_1_s[i] = strcat("output_3_1_",i,".txt");
}
file[] output_3_1 <array_mapper; files=output_3_1_s>;

output_3_1 = stage_3(input_shared_1_3,
                     output_2_2);


# -----------------------------------------------------------------------------
#
# Stage 4
#
app (file output_4_1) stage_4 (file   input_shared_1_5, 
                               file[] output_3_1)
{
    # 1 core
    stage_4_exe filename(input_shared_1_5) 
                @output_3_1;
}
file output_4_1  <"output_4_1.txt">;
output_4_1  = stage_4(input_shared_1_5,
                      output_3_1);

# -----------------------------------------------------------------------------

