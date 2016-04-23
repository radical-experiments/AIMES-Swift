
type file;

app (file sorted) sortdata (file unsorted)
{
    sort "-n" filename(unsorted) stdout=filename(sorted);
}

app (file reversed) reverse (file sorted)
{
    tac filename(sorted) stdout=filename(reversed);
}

file unsorted   <"unsorted.txt">;
file sorted     <"sorted.txt">;
file reversed   <"reversed.txt">;

sorted   = sortdata(unsorted);
reversed = reverse(sorted);

