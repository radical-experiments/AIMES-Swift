type file;

app (file out) remote_driver (int time)
{
   sleep time stdout=@out;
}

app (file out) remote_shuf (int time)
{
   shuf "-i 1-100" stdout=@out;
}

file driver_out[] <simple_mapper; prefix="date", suffix=".out">;

int count = toInt(arg("N", "1"));
int sleep = toInt(arg("sleep", "100"));

foreach i in [1:count] {
    driver_out[i] = remote_driver(sleep);
    //driver_out[i] = remote_shuf(sleep);
}

