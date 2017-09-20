
(define kfs #[0.5 1.0 4.5])

(define (calckf time kfs start num left right)
  (let* ([mid (quotient num 2)]
         [key (vector-ref kfs mid)])
    (printf "~s ~s ~s~n" mid start num)

    (cond [(= num 0) (cons left right)]
          [(and (= num 1) (not left) (not right)) ]
          [(< time key)
           (println "aaa")
           (calckf time kfs start (+ 1 (- mid start)) left mid)]
          [(> time  key)
           (println "bbb")
           (calckf time kfs (+ 1 mid) (- num mid 1) mid right)]
          [else  (cons mid mid)  ])

    ))




(calckf 3.0 kfs 0 (vector-length kfs) #f #f)
;; (or #f 5)
