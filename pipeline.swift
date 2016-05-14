
type file;

app (file sorted) sort (file unsorted)
{
    sort "-n" filename(unsorted) stdout=filename(sorted);
}

app (file reversed) reverse (file sorted)
{
    tac filename(sorted) stdout=filename(reversed);
}

int count = toInt(arg("N", "2"));

file sorted_all[];
file reversed_all[];

foreach i in [1:count] {
    file unsorted   <"unsorted.txt">;
    file sorted     <single_file_mapper; file=strcat("sorted.",i,".txt")>;
    sorted          = sort(unsorted);
    sorted_all[i]   = sorted;

}

foreach i in [1:count] {

    file reversed   <single_file_mapper; file=strcat("reversed.",i,".txt")>;
    
    reversed        = reverse(sorted_all[i]);
    reversed_all[i] = reversed;
}

