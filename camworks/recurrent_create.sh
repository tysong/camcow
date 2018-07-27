# Recurrently spins up and experiments and acquires the results based on a timer
GRACE=1800
CONTAINER=docker.monroe-system.eu/deployed/camcow_camworks
NODES="394 395 396 397 400 401 402 403 438 439 440 441 444 445 476 477 594 595 596 597 598 599 600 601 501 500 472 471 470 484"

while true
do
	EXP=$(monroe create $CONTAINER --deployed --nodes $NODES --duration $GRACE --traffic 30 --storage 30)
	echo "Spinning up experiment with ID $EXP and waiting $GRACE seconds to fetch..."
	sleep $(($GRACE+60))
	EXP_ID=$(echo $EXP | sed 's/[^0-9]*//g')
	monroe results $EXP_ID
	echo "Fetched results for $EXP_ID"
done	
