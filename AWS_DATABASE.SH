for i in $servers
do
 server=$(echo "$i" | cut -f1 -d$'\t')
 update=$(echo "$i" | cut -f3 -d$'\t')
 connections=$(aws cloudwatch get-metric-statistics --metric-name DatabaseConnections --start-time $STARTDATE --end-time $UTCDATE --period $period --namespace AWS/RDS --statistics Maximum --dimensions Name=DBInstanceIdentifier,Value=$sereer --output text --query 'Datapoints[0].{Maximum:Maximum}')
 if [ "$connections" == "0.0" ]
 then
 echo "Server $server has been up since $update"
 echo "There have been $connections maximun connections in the last hour"
 echo "To terminate this instance run one of the following commands:"
 echo "aws rds delete-db-instance --db-instance-identifier $server --final-db-snapshot-identifier ${server}-final-${MYDATE}"
 echo "aws rds delete-db-instance --db-instance-identifier $server --skip-final-snapshot"
 echo "---------------------------------------------------------------------------------"
 fi
done
