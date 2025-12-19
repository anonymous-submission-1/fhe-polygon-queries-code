package main

import (
	"fmt"
	"github.com/tuneinsight/lattigo/v6/circuits/ckks/minimax"
)

func main() {
	fmt.Println("Generating minimax composite polynomial for sign function...")
	//fmt.Println("Parameters:")
	//fmt.Println("  Precision: 256 bits")
	//fmt.Println("  Log Alpha: 30")
	//fmt.Println("  Log Error: 35") 
	//fmt.Println("  Degrees: [55, 59, 59]")
	fmt.Println()
	
	// Call the function with your specified parameters
	minimax.GenMinimaxCompositePolynomialForSign(256, 8, 8, []int{7, 15, 15})
	
	fmt.Println("Polynomial generation completed!")
}
