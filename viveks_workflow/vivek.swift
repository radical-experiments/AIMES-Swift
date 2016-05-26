
type file;

int N = toInt(arg("N", "512")); # 64 ... 2048
int chunk_size = 64; # chunksize for stage 3
int n_chunks   = 8; # number of chunks

int verb = 1;

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

    if (verb == 1) {
      # trace("stage 1");
      # trace(filename(input_shared_1_1));
      # trace(filename(input_shared_1_2));
      # trace(filename(input_shared_1_3));
      # trace(filename(input_shared_1_4));
      # trace(filename(input_shared_1_5));
    }

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
    
    if (verb == 1) {
      # trace("stage 2");
      # trace(filename(input_shared_1_3));
      # trace(filename(input_shared_1_4));
      # trace(filename(output_1_1[i]));
    }
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
app (file[] output_3_1) stage_3 (int    chunk, 
                                 int    chunksize, 
                                 file   input_shared_1_3, 
                                 file[] output_2_2)
{
    # N cores
    stage_3_exe chunk 
                chunksize
                filename(input_shared_1_3) 
                @output_2_2;
}

# we run stage_3 in chunks of C cores each, so we nee dto subdivide the file
# list into such chunks

# string[] output_3_1_s;   # output files for all chunks
# foreach i in [1:N] {
#     output_3_1_s[i] = strcat("output_3_1_",i,".txt");
# }
file[] output_3_1;

# over all chunks
foreach c in [0:(n_chunks-1)] {

    # file lists for chunk 
    file[]   output_2_2_c;     # input files for this chunk
    string[] output_3_1_c_s;   # output files for this chunk

    # over all chunk elements
    foreach i in [1:chunk_size] {

        # global index
        int j = c*chunk_size + i;
        output_2_2_c[i]   = output_2_2[j];
        output_3_1_c_s[i] = strcat("output_3_1_",j,".txt");
    }

    # convert into file sets
    file[] output_3_1_c <array_mapper; files=output_3_1_c_s>;

    # run this chunk
    if (verb == 1) {
        string tmp = sprintf("stage 3: %s : %s : %s -> %s", c, 
                             filename(input_shared_1_3), 
                             strjoin(output_2_2_c, " "), 
                             strjoin(output_3_1_c_s, " "));
        trace(tmp);

    }
    output_3_1_c = stage_3(c, chunk_size, 
                           input_shared_1_3,
                           output_2_2_c);

    # now merge the received files from the chunk into the global thing
    foreach i in [1:chunk_size] {

        # global index
        int j = c*chunk_size + i;
        output_3_1[j] = output_3_1_c[i];
    }
    
}


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

if (1 == 1) {

    if (verb == 1) {
        trace("stage 4");
        trace(filename(input_shared_1_5));
        trace(@output_3_1);
    }

    file output_4_1  <"output_4_1.txt">;
    output_4_1  = stage_4(input_shared_1_5,
                          output_3_1);
}

# -----------------------------------------------------------------------------

