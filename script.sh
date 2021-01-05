#for i in $(seq 1 5); do
	# (time ./client1 127.0.0.2 7007 1Mo 0 ) &> temp
	echo "Launching client..."
	(time ./client1 127.0.0.2 7007 1Mo 0) &> temp
	read -p "Press Enter when finished"

	# on calcule le débit
	t=$(cat temp 2>/dev/null | sed 's/,/./')
	moyenne=$(echo "scale=2; 1/$t" | bc -l 2>/dev/null)
	echo -e  "temps total = $t\t\t debit = $moyenne Mb/s"
#done
