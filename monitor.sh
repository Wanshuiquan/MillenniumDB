echo "start monitor"
LOG_FILE="mem.log"


# 监控 mdb-server 进程的内存使用情况
while pgrep -x "mdb-server" > /dev/null; do
    MEM_INFO=$(ps -eo pid,comm,%mem,rss,vsize --sort=-%mem | grep "mdb-server")
    echo "$(date) $MEM_INFO" >> "$LOG_FILE"
    sleep 10
done

echo "stop" 