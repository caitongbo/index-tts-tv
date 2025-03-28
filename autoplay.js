
    document.addEventListener('DOMContentLoaded', function() {
        function setupAutoPlay() {
            // 等待所有音频元素加载完成
            setTimeout(function() {
                const audioElements = document.querySelectorAll('audio');
                const audioPlayers = Array.from(audioElements);
                
                // 为每个音频元素添加结束事件监听器
                audioPlayers.forEach((player, index) => {
                    player.addEventListener('ended', function() {
                        // 当前音频播放结束后，查找下一个音频元素并播放
                        const nextIndex = index + 1;
                        if (nextIndex < audioPlayers.length) {
                            // 确保下一个音频元素是可见的
                            const nextPlayer = audioPlayers[nextIndex];
                            if (nextPlayer && !nextPlayer.paused) {
                                nextPlayer.play();
                            }
                        }
                    });
                });
                
                console.log('自动播放功能已设置');
            }, 2000); // 给页面元素加载的时间
        }
        
        // 当DOM加载完成后设置自动播放
        setupAutoPlay();
        
        // 当内容更新时重新设置自动播放
        document.addEventListener('click', function(e) {
            if (e.target && (e.target.textContent === '一键生成' || 
                            e.target.textContent.includes('生成句子'))) {
                setTimeout(setupAutoPlay, 2000);
            }
        });
    });
    